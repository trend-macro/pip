import sys
import re
import textwrap
import pytest
from doctest import OutputChecker, ELLIPSIS

from tests.lib import _create_test_package, _create_test_package_with_srcdir


distribute_re = re.compile('^distribute==[0-9.]+\n', re.MULTILINE)


def _check_output(result, expected):
    checker = OutputChecker()
    actual = str(result)

    # FIXME!  The following is a TOTAL hack.  For some reason the
    # __str__ result for pkg_resources.Requirement gets downcased on
    # Windows.  Since INITools is the only package we're installing
    # in this file with funky case requirements, I'm forcibly
    # upcasing it.  You can also normalize everything to lowercase,
    # but then you have to remember to upcase <BLANKLINE>.  The right
    # thing to do in the end is probably to find out how to report
    # the proper fully-cased package name in our error message.
    if sys.platform == 'win32':
        actual = actual.replace('initools', 'INITools')

    # This allows our existing tests to work when run in a context
    # with distribute installed.
    actual = distribute_re.sub('', actual)

    def banner(msg):
        return '\n========== %s ==========\n' % msg

    assert checker.check_output(expected, actual, ELLIPSIS), (
        banner('EXPECTED') + expected + banner('ACTUAL') + actual +
        banner(6 * '=')
    )


def test_drugs_basic(script):
    """
    Some tests of drugs, first we have to install some stuff.  Note that
    the test is a little crude at the end because Python 2.5+ adds egg
    info to the standard library, so stuff like wsgiref will show up in
    the freezing.  (Probably that should be accounted for in pip, but
    currently it is not).

    """
    script.scratch_path.join("initools-req.txt").write(textwrap.dedent("""\
        simple==2.0
        # and something else to test out:
        simple2<=3.0
        """))
    script.pip_install_local(
        '-r', script.scratch_path / 'initools-req.txt',
    )
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent("""\
        ...simple==2.0
        simple2==3.0...
        <BLANKLINE>""")
    _check_output(result.stdout, expected)


def test_drugs_with_pip(script):
    """Test pip shows itself"""
    result = script.pip('drugs', '--all')
    assert 'pip==' in result.stdout


@pytest.mark.svn
def test_drugs_svn(script, tmpdir):
    """Test freezing a svn checkout"""

    checkout_path = _create_test_package(script, vcs='svn')

    # Install with develop
    script.run(
        'python', 'setup.py', 'develop',
        cwd=checkout_path, expect_stderr=True
    )
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent("""\
        ...-e svn+...#egg=version_pkg
        ...""")
    _check_output(result.stdout, expected)


@pytest.mark.git
def test_drugs_git_clone(script, tmpdir):
    """
    Test freezing a Git clone.
    """
    # Returns path to a generated package called "version_pkg"
    pkg_version = _create_test_package(script)

    result = script.run(
        'git', 'clone', pkg_version, 'pip-test-package',
        expect_stderr=True,
    )
    repo_dir = script.scratch_path / 'pip-test-package'
    result = script.run(
        'python', 'setup.py', 'develop',
        cwd=repo_dir,
        expect_stderr=True,
    )
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent(
        """
            ...-e git+...#egg=version_pkg
            ...
        """
    ).strip()
    _check_output(result.stdout, expected)

    result = script.pip(
        'drugs', '-f', '%s#egg=pip_test_package' % repo_dir,
        expect_stderr=True,
    )
    expected = textwrap.dedent(
        """
            -f %(repo)s#egg=pip_test_package...
            -e git+...#egg=version_pkg
            ...
        """ % {'repo': repo_dir},
    ).strip()
    _check_output(result.stdout, expected)

    # Check that slashes in branch or tag names are translated.
    # See also issue #1083: https://github.com/pypa/pip/issues/1083
    script.run(
        'git', 'checkout', '-b', 'branch/name/with/slash',
        cwd=repo_dir,
        expect_stderr=True,
    )
    # Create a new commit to ensure that the commit has only one branch
    # or tag name associated to it (to avoid the non-determinism reported
    # in issue #1867).
    script.run('touch', 'newfile', cwd=repo_dir)
    script.run('git', 'add', 'newfile', cwd=repo_dir)
    script.run('git', 'commit', '-m', '...', cwd=repo_dir)
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent(
        """
            ...-e ...@...#egg=version_pkg
            ...
        """
    ).strip()
    _check_output(result.stdout, expected)


@pytest.mark.git
def test_drugs_git_clone_srcdir(script, tmpdir):
    """
    Test freezing a Git clone where setup.py is in a subdirectory
    relative the repo root and the source code is in a subdirectory
    relative to setup.py.
    """
    # Returns path to a generated package called "version_pkg"
    pkg_version = _create_test_package_with_srcdir(script)

    result = script.run(
        'git', 'clone', pkg_version, 'pip-test-package',
        expect_stderr=True,
    )
    repo_dir = script.scratch_path / 'pip-test-package'
    result = script.run(
        'python', 'setup.py', 'develop',
        cwd=repo_dir / 'subdir',
        expect_stderr=True,
    )
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent(
        """
            ...-e git+...#egg=version_pkg&subdirectory=subdir
            ...
        """
    ).strip()
    _check_output(result.stdout, expected)

    result = script.pip(
        'drugs', '-f', '%s#egg=pip_test_package' % repo_dir,
        expect_stderr=True,
    )
    expected = textwrap.dedent(
        """
            -f %(repo)s#egg=pip_test_package...
            -e git+...#egg=version_pkg&subdirectory=subdir
            ...
        """ % {'repo': repo_dir},
    ).strip()
    _check_output(result.stdout, expected)


@pytest.mark.mercurial
def test_drugs_mercurial_clone(script, tmpdir):
    """
    Test freezing a Mercurial clone.

    """
    # Returns path to a generated package called "version_pkg"
    pkg_version = _create_test_package(script, vcs='hg')

    result = script.run(
        'hg', 'clone', pkg_version, 'pip-test-package',
        expect_stderr=True,
    )
    repo_dir = script.scratch_path / 'pip-test-package'
    result = script.run(
        'python', 'setup.py', 'develop',
        cwd=repo_dir,
        expect_stderr=True,
    )
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent(
        """
            ...-e hg+...#egg=version_pkg
            ...
        """
    ).strip()
    _check_output(result.stdout, expected)

    result = script.pip(
        'drugs', '-f', '%s#egg=pip_test_package' % repo_dir,
        expect_stderr=True,
    )
    expected = textwrap.dedent(
        """
            -f %(repo)s#egg=pip_test_package...
            ...-e hg+...#egg=version_pkg
            ...
        """ % {'repo': repo_dir},
    ).strip()
    _check_output(result.stdout, expected)


@pytest.mark.bzr
def test_drugs_bazaar_clone(script, tmpdir):
    """
    Test freezing a Bazaar clone.

    """
    try:
        checkout_path = _create_test_package(script, vcs='bazaar')
    except OSError as e:
        pytest.fail('Invoking `bzr` failed: %s' % e)

    result = script.run(
        'bzr', 'checkout', checkout_path, 'bzr-package'
    )
    result = script.run(
        'python', 'setup.py', 'develop',
        cwd=script.scratch_path / 'bzr-package',
        expect_stderr=True,
    )
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent("""\
        ...-e bzr+file://...@1#egg=version_pkg
        ...""")
    _check_output(result.stdout, expected)

    result = script.pip(
        'drugs', '-f',
        '%s/#egg=django-wikiapp' % checkout_path,
        expect_stderr=True,
    )
    expected = textwrap.dedent("""\
        -f %(repo)s/#egg=django-wikiapp
        ...-e bzr+file://...@...#egg=version_pkg
        ...""" % {'repo': checkout_path})
    _check_output(result.stdout, expected)


def test_drugs_with_local_option(script):
    """
    Test that wsgiref (from global site-packages) is reported normally, but not
    with --local.
    """
    result = script.pip_install_local('initools==0.2')
    result = script.pip('drugs', expect_stderr=True)
    expected = textwrap.dedent("""\
        INITools==0.2
        wsgiref==...
        <BLANKLINE>""")

    # The following check is broken (see
    # http://bitbucket.org/ianb/pip/issue/110).  For now we are simply
    # neutering this test, but if we can't find a way to fix it,
    # this whole function should be removed.

    # _check_output(result, expected)

    result = script.pip('drugs', '--local', expect_stderr=True)
    expected = textwrap.dedent("""\
        INITools==0.2
        <BLANKLINE>""")
    _check_output(result.stdout, expected)


def test_drugs_with_requirement_option(script):
    """
    Test that new requirements are created correctly with --requirement hints

    """
    ignores = textwrap.dedent("""\
        # Unchanged requirements below this line
        -r ignore.txt
        --requirement ignore.txt
        -Z ignore
        --always-unzip ignore
        -f http://ignore
        -i http://ignore
        --pre
        --trusted-host url
        --process-dependency-links
        --extra-index-url http://ignore
        --find-links http://ignore
        --index-url http://ignore
        """)
    script.scratch_path.join("hint.txt").write(textwrap.dedent("""\
        INITools==0.1
        NoExist==4.2
        simple==3.0; python_version > '1.0'
        """) + ignores)
    result = script.pip_install_local('initools==0.2')
    result = script.pip_install_local('simple')
    result = script.pip(
        'drugs', '--requirement', 'hint.txt',
        expect_stderr=True,
    )
    expected = """\
INITools==0.2
simple==3.0
""" + ignores + "## The following requirements were added by pip drugs:..."
    _check_output(result.stdout, expected)
    assert (
        "Requirement file contains NoExist==4.2, but that package is not "
        "installed"
    ) in result.stderr


def test_drugs_user(script, virtualenv):
    """
    Testing drugs with --user, first we have to install some stuff.
    """
    virtualenv.system_site_packages = True
    script.pip_install_local('--user', 'simple==2.0')
    script.pip_install_local('simple2==3.0')
    result = script.pip('drugs', '--user', expect_stderr=True)
    expected = textwrap.dedent("""\
        simple==2.0
        <BLANKLINE>""")
    _check_output(result.stdout, expected)
    assert 'simple2' not in result.stdout
