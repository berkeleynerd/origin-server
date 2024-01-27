## Origin Server

This repo represents the server bits from a hard-fork of [Irmen's](https://github.com/irmen) awesome (and now sadly defunct) [Tale](https://github.com/irmen/Tale) IF/MUD framework. In addition to breaking out the back-end I've also simplified the code and hacked everything to fit my minimalist aesthetic liking.

## Motivation

The world clearly needs another a Multi-User Dungeon. Seriously though, why should Interactive Fiction and Multi-User Dungeons be mutually exclusive affairs? Did we learn nothing from all those "taste great together" commercials from our childhood? I think we can do better *and* bring it all together with a nice GUI for designing the world to boot. And let's throw a web-based interface in while we're at it in additional to the traditional telnet interface we all know and love. All right then, let's do it!

## Installation

Good luck! :)

## License

You're totally free download and use this code for anything as long as you never reveal I had anything to do with it and don't hold me legally liable for any light rail systems you decide to hack and upload it to so it can run off the switching system's PLC controllers. That's completely on you. Make sure you give [Irmen](https://github.com/irmen) major props!

## Game Object Hierarchy

    ObjectBase
      |
      +-- Location
      |
      +-- Item
      |     |
      |     +-- Weapon
      |     +-- Armour
      |     +-- Container
      |     +-- Key
      |
      +-- Creature
      |     |
      |     +-- Player
      |     +-- NPC
      |
      +-- Exit
            |
            +-- Door


Every object that can hold other objects does so in its "inventory" (a set).
You can't access it directly, object.inventory returns a frozenset copy of it.
Except Location: it separates the items and creatures it contains internally.
Use its enter/leave methods instead.
