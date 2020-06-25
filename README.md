Firefly
=======

Firefly is a desktop client application for [Nebula](https://github.com/nebulabroadcast/nebula) broadcast automation system.



Installation
------------

### Linux

Install **python3** and **python3-pip** packages and then install requiered libraries using
following command:

```
sudo pip3 install PyQT5 websocket-client
```

For video playback, you will also need **libmpv1** package.

### Windows

Latest binary release is available on [nebulabroadcast/firefly](https://github.com/nebulabroadcast/firefly/releases)
GitHub releases page.

[Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=52685)
is required to run this application.

Configuration
-------------

Edit **settings.json** file to set your server address and site name.

```json
{
    "sites"  : [{
        "site_name" : "nebulatv",
        "hub" : "https://nebulatv.example.com"
    }]
}
```

It is possible to specify more than one site in the settings.json file.
In that case, a dialog window pops up when the application is started and a site may be selected for this session.

`site_name` argument can be used as an indentifier for different configurations of the same site and its value
is updated when server settings are loaded.

Usage
-----

### Keyboard shortcuts

Shortcut       | Scope      |  Description
---------------|------------|-----------------------------
ESC            | Global     | Focus browser search
F1             | Global     | Switch to rundown, go to now
F2             | Global     | Toggle asset detail
F5             | Global     | Refresh views
Ctrl+T         | Global     | Open new browser tab
Ctrl+W         | Global     | Close current browser tab
Ctrl+PgUp      | Global     | Switch to previous tab
Ctrl+PgDown    | Global     | Switch to next tab
Ctrl+N         | Global     | Create new asset
Ctrl+Shift+N   | Global     | Clone current asset
Alt+Left       | Scheduler  | Previous week
Alt+Right      | Scheduler  | Next week
Alt+Left       | Rundown    | Previous day
Alt+Right      | Rundown    | Next day
Ctrl+D         | Rundown    | Show calendar
Ctrl+F         | Rundown    | Search in rundown
Ctrl+R         | Rundown    | Toggle rundown edit mode
F3             | Rundown    | Search in rundown again
Ctrl+J         | MCR        | Cue previous item
Ctrl+K         | MCR        | Take
Ctrl+L         | MCR        | Cue next item
Alt+J          | MCR        | Retake
Alt+K          | MCR        | Freeze
Alt+L          | MCR        | Abort
1, J           | Preview    | Seek previous 5 frames
2, L           | Preview    | Seek next 5 frames
3, Left        | Preview    | Seek previous frame
4, Right       | Preview    | Seek next frame
A, Home        | Preview    | Go to start
S, End         | Preview    | Go to end
Q              | Preview    | Go to in
W              | Preview    | Go to out
E, I           | Preview    | Mark in
R, O           | Preview    | Mark out
D              | Preview    | Clear in
F              | Preview    | Clear out
Space, K       | Preview    | Play/pause
Ctrl+S         | Detail     | Save changes/create asset
Y              | Detail     | Mark asset as approved
T              | Detail     | Reset QC state
U              | Detail     | Mark asset as rejected


### Troubleshooting

> Have you tried turning it off and on again?

In most cases, this helps. If the application worked and suddenly it is not possible
to start, try to delete `ffdata` files in its directory and start it again.
