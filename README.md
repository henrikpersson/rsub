# rsub

## Description

Rsub is an implementation of TextMate 2's '[rmate](https://github.com/textmate/rmate)' feature for Sublime Text 2,
allowing files to be edited on a remote server using SSH port forwarding /
tunnelling.

Included in this repository are two implementations of the 'rmate' command, the
original written in Ruby, and another version written using bash scripting.
You will need to choose and copy one of these up to your server, usually with
scp, sftp, or plain FTP. See the README file inside rmate-bash for more detail.

## Installation

You can install this plugin using sublime package control.
It will keep all your plugins up to date.
http://wbond.net/sublime_packages/package_control

-------------------------
OR

You can also clone this repository into the Sublime Text 2 'Packages'
directory, but you will have to update it manually.

On Mac OS X, this is located at
`~/Library/Application Support/Sublime Text 2/Packages`.

Run the following commands in Terminal, then restart Sublime Text 2:

    cd ~/Library/Application\ Support/Sublime\ Text 2/Packages
    git clone git://github.com/henrikpersson/rsub.git rsub
    
## SSH tunneling

Due to security reasons, rsub is only listening for local connections.

Simply put this in your ~/.ssh/config to enable remote forwarding for your server(s):

    Host example.com
        RemoteForward 52698 127.0.0.1:52698

## Usage

Once you have `rmate` installed on your remote server (installation instructions can be found [here](https://github.com/textmate/rmate)), `rsub` installed on your local machine and an ssh tunnel open, execute the following command on your __remote server__ to edit files in SublimeText:

    rmate <filename>

More information on command line options can be found in the [rmate repository](https://github.com/textmate/rmate).
