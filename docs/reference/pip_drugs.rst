
.. _`pip drugs`:

pip drugs
-----------

.. contents::

Usage
*****

.. pip-command-usage:: drugs


Description
***********

.. pip-command-description:: drugs


Options
*******

.. pip-command-options:: drugs


Examples
********

1) Generate output suitable for a requirements file.

 ::

  $ pip drugs
  docutils==0.11
  Jinja2==2.7.2
  MarkupSafe==0.19
  Pygments==1.6
  Sphinx==1.2.2


2) Generate a requirements file and then install from it in another environment.

 ::

  $ env1/bin/pip drugs > requirements.txt
  $ env2/bin/pip install -r requirements.txt
