# Light Scenes Plugin for Indigo

The Light Scenes plugin supports creation of customized scenes. The plugin is compatible with the Indigo 'Dimmer' device type. Hence any device based on Indigo Dimmer should work. 

The Circadian scene is my favorite and most used in the household :). I have several Dimmers(or groups) in my house and the Circadian scene provides perfect lighting. Late night and early morning the lights are dim and yellow/orange-ish. They ramp-up in the morning to be bright and more white/blu-ish. Hence if you are concerned about too much blue light at night before bed, this scene has you covered.

### Plugin Features
* Scenes - creation of customized lighting scenes as pre-defined settings/sequences of on/off/brightness/white/rgb:
  * 'Circadian' - automatically sets the Dimmer based on time of day to match a configurable 'circadian rhythm'.
  * 'Match Color/Temp' - matches the color/temp/brightness. Rotates the dimmer (or group) through each of the different colors specified in the scene.
  
### Supported Device Types

* Indigo Dimmer Device Type
The plugin can operate against any Indigo Dimmer device type. Vendor-specific lighting Indigo plugins expose a 'Group' of lights as a single Indigo Dimmer. As such, the scenes work fine, and will set all of the lights in the group to the same color/temp/brightness values. I've used the plugin with Hue, Sylvania Lightify, and standard non-color/white bulbs.

### Disclosures

* Edit Scenes UX Disclaimer: The Edit Scenes UX could use some help. Apologies for the funky comma-separated values and need to lookup RGB/Color Temp charts. One of these days if there is enough interest in the plugin I may finally spend some time to figure out the color picker UI and integrate it into the plugin. If you are a pro at this stuff and would like to collaborate, feel free to reach out.

* Best Effort implementation: The plugin current does a 'best-effort' implementation and attempts to update whatever settings are available for the device. For example, you could technically use the 'Circadian' scene for Dimmers that don't actually do Color Temps. In this scenario, the plugin will simply update the brightness and skip color temp changes. 

[1]: https://github.com/rbdubz3/light-scenes-indigo/wiki
[2]: https://github.com/rbdubz3/light-scenes-indigo/releases
[3]: http://www.indigodomo.com