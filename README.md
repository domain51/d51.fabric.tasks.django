d51.fabric.tasks.django
=========================
Fabric tasks for handling basic management tasks for Django


Requirements
------------
This has been built to be used with the 1.0a version of the [Fabric fork][]
maintained by [Travis Swicegood][].  It might be usable with other versions of
Fabric, but your mileage may vary.


Installation
------------
Create a clone of the repository:

    git clone git://github.com/domain51/d51.fabric.tasks.django.git

Then, inside that directory you can install it using either the `setup.py` file
directly, or via Fabric:

    prompt> python setup.py install
    ... or ...
    prompt> fab install

Usage
-----
You can import the individual tasks into your current fabfile:

    from d51.fabric.tasks.django import *

Or, you can import the module and execute the tasks that way:

    from d51.fabric.tasks import django


Tasks
-----
_TODO_

[Fabric fork]: http://github.com/tswicegood/fabric
[Travis Swicegood]: http://www.travisswicegood/
