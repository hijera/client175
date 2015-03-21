# Introduction #

This page describes how to run client175 behind an existing Apache installation using mod\_python.  Client175 version 0.6 or greater is required for this to work.

Why would you do this?  Primarily, because you already have Apache running for other reasons and you want to integrate client175 into that installation rather than running another web server.  There is no reason to install Apache _just_ to run this client.

These instructions are based on Ubuntu.



## Install mod\_python ##

If you don't already have it, install mod\_python from your distribution's repository.  For example:

`sudo apt-get install libapache2-mod-python`

Create a symlink from /etc/apache2/mods-available to /etc/apache2/mods-enabled for mod\_python.  On Ubuntu that would be:

`ln -s /etc/apache2/mods-available/python.load /etc/apache2/mods-enabled`


## Extract/Copy client175 Package ##

Extract the contents of the client175 package or copy the files from an existing location to the appropriate location for your setup.  On my PC, that location is /var/www/client175.



## Edit "server\_root" in site.conf ##

The site.conf file in the client175 root folder contains various optional settings, including the server\_root option.  If you wish to have client175 available in a sub folder of your Apache install, uncomment that line and set it to the path you would like to use.

If you haven't already edited the music\_directory option to point to your music folder, you should do that also to enable tag editing.



## Edit httpd.conf ##

Usually found in /etc/apache2.  You'll need to set the location section for client175.  Here is a complete file for an apache install running just client175:

```
Listen 8080
<Location "/client175">
    PythonPath "['/var/www/client175', '/var/www/client175/cherrypy']+ sys.path"
    SetHandler python-program
    PythonHandler cherrypy._cpmodpy::handler
    PythonOption cherrypy.setup server::serverless
    PythonDebug On
</Location>
```

This will make the site available at `http://localhost:8080/client175`.

The important variables here are the path specified in the opening Location tag and the PythonPath.  The path in the Location tag must match the path specified as the server\_root in site.conf.  The PythonPath must include the path to where client175 has been extracted to.  If you have CherryPy 3.1+ installed, you don't have to include the path to the CherryPy package that comes included with client175.



## Assign Read/Write Access to the Apache User ##

The account that Apache runs under needs to have read/write access to the location where client175 is installed.  In this example, I have extracted it to /var/www/client175.  On Ubuntu, the default Apache user is www-data:

`sudo chown -R www-data /var/www/client175`



## Restart Apache ##

`sudo /etc/init.d/apache2 restart`

Apache will handle serving the site completely in this setup, so you should not start the included server manually or via any upstart/init scripts.

The most likely cause of problems will be permissions.  Ensure that the user Apache runs under can create files in the location client175 is installed to.