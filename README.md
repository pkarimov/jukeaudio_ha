This is a Home Assistant integration for the Juke Audio multi-zone amplifiers.

* HACS compliant repository 

Installation
============

## Install HACS
- If you have not yet installed HACS, go get it at [https://hacs.xyz](https://hacs.xyz/) and walk through the installation and configuration.

## Install the Juke Audio Repository
You can install this either manually copying files or using HACS. Configuration can be done on UI, you need to enter your username and password

## Add the Juke Audio Integration
- In Home Assistant, select Configuration / Integrations / Add Integration.
- Search for 'Juke Audio' and add the integration.

## Configure the connection
![image](https://github.com/pkarimov/jukeaudio_ha/assets/72779542/83496091-4b02-4bab-988f-0915619d216f)

### Configuration
- Host: IP address of your Juke amplifier. The default value is 'juke.local', it may not work depending on your network setup.
- Username: Admin is the default user name for Juke amplifiers
- Password: Use the same password you configured via Administrator Settings on the amplifier
- Scan Interval: how often you want Home Assistant to fetch values from the amplifier

Usage
=====

This integration creates Media Player entities for each of the amplifier zones, Select entities for the different inputs, and diagnostic sensors for monitoring hardware and network. For each zone you can control the Juke source it is mapped to and volume. You can use the Input entities to switch between different input types supported by your Juke.
