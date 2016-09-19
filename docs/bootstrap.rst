.. currentmodule:: sgtk.bootstrap

Deploy and management
########################################

This section outlines the various ways to set up, configure and initialize a Toolkit Setup.
There are two fundamental approaches to running Toolkit: A traditional project based setup
and a :class:`ToolkitManager` API that allows for more flexible manipulation of
configurations and installations.

Traditional project setup
----------------------------------------

The traditional Toolkit 'pipeline approach' means that you pick an existing Shotgun
project and run a Toolkit project setup for this project. This is typically done in
Shotgun Desktop or via the ``tank setup_project`` command. A Toolkit configuration
is installed in a shared location on disk and a pipeline configuration in Shotgun is
created to create an association between the installation on disk and the project in
Shotgun.

Once the installation has completed, you can access functionality via the ``tank`` command
for that project or run :meth:`sgtk.sgtk_from_entity()` or :meth:`sgtk.sgtk_from_path()`
in order to create an API session.

    .. note:: For more information about how to set up a traditional toolkit project,
              please see our administrator guides at https://support.shotgunsoftware.com.


Bootstrapping Toolkit
----------------------------------------

An alternative to the traditional project based setup was introduced in Core v0.18 - the
:class:`ToolkitManager` class allows for more flexible manipulation of toolkit setups
and removes the traditional step of a project setup. Instead, you can create a Toolkit plugin
which contains internal logic to launch an engine
directly based on a Toolkit configuration. The :class:`ToolkitManager` encapsulates the deploy
and configuration management process and makes it easy to create a running instance of
Toolkit. It allows for several advanced use cases:


- A setup can be pre-bundled with a DCC plugin, allowing
  Toolkit to act as a distribution platform.

- Bootstrapping via the :class:`ToolkitManager` does not require anything to be
  set up or configured in Shotgun. No extensive project setup step is required.

- The :class:`ToolkitManager` makes it easy to track remote resources
  (via the ``sgtk.descriptor`` framework). You can easily develop a plugin which
  auto-updates its apps from git or Shotgun.

- The :class:`ToolkitManager` makes it easier to integrate Toolkit with external
  systems such as `Res <https://github.com/nerdvegas/rez/wiki>`_

The following example code can for example run inside maya in order
to launch Toolkit's default config for a given Shotgun Asset::

    import sgtk

    # Start up a Toolkit Manager
    mgr = sgtk.bootstrap.ToolkitManager()

    # Set the base configuration to the default config
    # note that the version token is not specified
    # The bootstrap will always try to use the latest version
    mgr.base_configuration = "sgtk:descriptor:app_store?name=tk-config-default"

    # now start up the maya engine for a given Shotgun object
    e = mgr.bootstrap_engine("tk-maya", entity={"type": "Asset", "id": 1234})

Note that the example is primitive and for example purposes only as it will take time to execute
and blocks execution during this period.

In this example, there is no need to construct any :class:`sgtk.Sgtk` instance or run a ``tank``
command - the :class:`ToolkitManager` instead becomes the entry point into the system. It will
handle the setup and initialization of the configuration behind the scenes
and start up a Toolkit session once all the required pieces have been initialized and set up.

ToolkitManager
========================================

.. autoclass:: ToolkitManager
    :members:
    :inherited-members:
    :exclude-members: entry_point, set_progress_callback

Exception Classes
========================================

.. autoclass:: TankBootstrapError


Developing Plugins
----------------------------------------







Creating a plugin
=========================================

There are several options here you can choose between:

1.       Minimal build: The plugin doesn’t come with any payload at all. In order to get started, the user needs to be connected to the internet to download an initial update. During subsequent runs, the plugin will check if an update is available and in that case download it on the fly. We don’t recommend using this approach unless it is critical that the plugin is as small as possible.

2.       Auto-updating build: The plugin comes bundled with all the pieces it needs. On startup, the plugin will try to connect to the internet and check if an update is available. If it is, it will download it automatically. If no internet is available, the latest local version is used. We consider this the “default” mode and it means you can very easily push updates to the integration. This could easily be wired up for example with a “automatically check for updates” checkbox in the settings. For this, you would need to push your config and apps to the toolkit app store.

3.       Baked build: Plugin never checks for updates. Always uses whatever came with the plugin. This is how RV works. This setup means fewer moving parts and you know *exactly* what clients are running, but the option of auto update goes away.

In addition to the above, each plugin can define if it allows Shotgun to override the configuration or not. I am guessing in your case, you want to set this to False, where for example in the case of the more general pipeline integration in Maya, this is typically set to true, allowing studios to take control over the config.

Hope this makes sense! I am working on developer docs right now, coming soon!

In addition to the above, we are just about to release a new tk core which supports handling the update checking in a background worker thread. This makes it possible to wrap any update with some nice UX.


- plugin id

- naming convention for folders



Building a plugin
========================================


.. code-block:: bash

    #!/bin/bash

    #############################################
    # Example bash build script for automated plugin build
    # This script will do the following:
    #
    # 1. download the latest toolkit core (master branch)
    # 2. download the latest plugin repository
    # 3. run the build script
    #
    # NOTE: The script connects to the toolkit app store during
    #       execution and therefore needs you to pass in an API
    #       script user and script key for your shotgun site.
    #
    #       if you omit the authentication parameters, the script
    #       will prompt you for a login and password at runtime.

    engine_name="tk-maya"
    plugin_name="basic"
    sg_site="https://MYSITE.shotgunstudio.com"
    sg_script=SCRIPTNAME
    sg_key=SCRIPTKEY

    # create temp folder
    build_folder=`mktemp -d`
    cd $build_folder

    echo "Downloading core..."
    git clone git@github.com:shotgunsoftware/tk-core.git

    echo "Downloading plugin source code..."
    git clone git@github.com:shotgunsoftware/${engine_name}.git

    echo "Building plugin..."
    cd tk-core/developer
    python build_plugin.py ../../${engine_name}/plugins/${plugin_name} ../../plugin_build -s ${sg_site} -n ${sg_script} -k ${sg_key}

    echo "Build complete in $build_folder/plugin_build"
    echo ""



Doing plugin development
========================================


``TK_BOOTSTRAP_CONFIG_OVERRIDE``



Configuration resolve order
========================================


The following resolution order will be attempted:

First toolkit will check for a project level, user associated pipeline configuration with

PipelineConfig.users field containing john smith
PipelineConfig.project field set to project 123
PipelineConfig.plugin_id matching test.maya
Next it will check for any user associated pipeline config with matching plugin id:

PipelineConfig.users field containing john smith
PipelineConfig.plugin_id matching test.maya
Next it will check for a project level primary config:

PipelineConfig.code field set to Primary
PipelineConfig.project field set to project 123
PipelineConfig.plugin_id matching test.maya
Next it checks for a primary config matching plugin id:

PipelineConfig.code field set to Primary
PipelineConfig.plugin_id matching test.maya
if none of the above returns a valid config, it falls back on the base config.




