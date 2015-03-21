# Introduction #

If you already have cherokee server running on your box and want to use it to access client175 then you are on the right page.

# Client175 Setup #

Setup you client175 installation and configure your site.conf like you will do for a standalone server


# Cherokee Setup #
All the configuration is done through cherokee-admin. this page assume you know how to use it.

## Sources ##
Click on the "Sources" tab in cherokee-admin and select "New".
Put Client175 in name and 127.0.0.1:port in the connection (port being the port you setup in site.conf)

Then validate and fill the fields like the picture.

![http://ftp.clemworkbench.fr/sources.png](http://ftp.clemworkbench.fr/sources.png)

The interpreter field should be filled with

` /usr/bin/python /path-to-client175/server.py`

The source is now configured and we just have to configure a new virtual server.

## VServer ##

It is likely that you will want to setup a new vserver for client175 (http://client175.yourhost.com/ for instance).

To begin, add a new VServer as you would do for a normal vserver.
Once it is done, select the behavier tab of your VServer and click on the "Default" rule. Then click on the handler tab and select "HTTP Reverse Proxy". Now complete the fields with the following informations :

![http://ftp.clemworkbench.fr/vserver.png](http://ftp.clemworkbench.fr/vserver.png)

Be sure to check the Preserve Host Header checkbox.
You can now click on save and perform a hard restart of cherokee.

# Accessing client175 #

The setup is now complete and client 175 should be accessible. Point your browser at http://your-vserver-name/static/index.html
The first launch will take some times as cherokee will launch the client175 server.