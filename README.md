# Welcome to Novel Online World!![Pangolin in motion](https://github.com/Pinacolada64/NOW/blob/master/web/static/website/images/NOW-icon.png)

This directory is the directory that contains the NOW assets in
development, and does not actually mirror the operating NOW server.

If you are cloning NOW, be aware that this is the customized code
in development, and not the full code for the server.

The prerequisite install of the latest Evennia is required. Be aware
that NOW runs atop Evennia in a separate game folder named NOW.

# Getting started with Evennia's install

It's highly recommended that you look up Evennia's extensive
documentation found here: https://github.com/evennia/evennia/wiki.

Plenty of beginner's tutorials can be found here:
http://github.com/evennia/evennia/wiki/Tutorials.

Install Evennia as normal, up to the point where the `evennia` command is working in your virtualenv.
    
    git clone https://github.com/Pinacolada64/NOW.git # create a new cloned NOW folder
    cd NOW
    
We already include a `settings.py` file, but you can do

    evennia --init settings

To start a new one in `NOW/server/conf/`
(Please don't forget to change `SECRET_KEY`, as it allows for more safety)

If you have no existing database for your game, `cd NOW` then
 initialize a new database using:

    evennia migrate

To start the server run

    evennia start

You will see console output, but can disconnect with `Control` + `D`, or `exit`.
Evennia stays running in daemon mode and displays output to the console.

Make sure to create a superuser when asked. By default you can now
connect using a MUD client on localhost:4000.  You can also use 
the web client by pointing a browser to

    http://localhost:8000
