Firefly
=======

Firefly is a desktop client application for [Nebula](https://github.com/nebulabroadcast/nebula) broadcast automation system.

Configuration
-------------

Edit **settings.json** file to set your server address and site name.

```json
{
    "sites"  : [{
        "site_name" : "demo",
        "hub" : "https://demo.nebulabroadcast.com"
    }]
}
```


Installation
------------

### Linux

Install **python3** and **python3-pip** packages and then install requiered libraries using
following command:

```
sudo pip3 install requests PyQT5 websocket-client
```

For video playback, you will also need **libmpv1** package.

### Windows

Latest binary release is available on [nebulabroadcast/firefly](https://github.com/nebulabroadcast/firefly/releases)
GitHub releases page.

[Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=52685)
is required to run this application.

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
F3             | Rundown    | Search in rundown again
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
