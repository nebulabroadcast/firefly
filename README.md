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
following command

```
sudo pip install requests PyQT5 websocket-client
```

For video playback, you will also need **libmpv1** package.

### Windows

Latest binary release is available on nebulabroadcast/firefly GitHub releases page.


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
