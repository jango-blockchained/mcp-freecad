Allowed options for command line with freecad:

Generic options:
  -v [ --version ]          Prints version string
  --verbose                 Prints verbose version string
  -h [ --help ]             Prints help message
  -c [ --console ]          Starts in console mode
  --response-file arg       Can be specified with '@name', too
  --dump-config             Dumps configuration
  --get-config arg          Prints the value of the requested configuration key
  --set-config arg          Sets the value of a configuration key
  --keep-deprecated-paths   If set then config files are kept on the old 
                            location

Configuration:
  -l [ --write-log ]        Writes FreeCAD.log to the user directory.
  --log-file arg            Unlike --write-log this allows logging to an 
                            arbitrary file
  -u [ --user-cfg ] arg     User config file to load/save user settings
  -s [ --system-cfg ] arg   System config file to load/save system settings
  -t [ --run-test ] arg     Run a given test case (use 0 (zero) to run all 
                            tests). If no argument is provided then return list
                            of all available tests.
  -r [ --run-open ] arg     Run a given test case (use 0 (zero) to run all 
                            tests). If no argument is provided then return list
                            of all available tests.  Keeps UI open after 
                            test(s) complete.
  -M [ --module-path ] arg  Additional module paths
  -P [ --python-path ] arg  Additional python paths
  --single-instance         Allow to run a single instance of the application
  --safe-mode               Force enable safe mode
  --pass arg                Ignores the following arguments and pass them 
                            through to be used by a script