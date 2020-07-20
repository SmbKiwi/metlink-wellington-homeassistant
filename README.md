[![Build Status](https://travis-ci.org/Br3nda/metlink-wellington-homeassistant.svg?branch=master)](https://travis-ci.org/Br3nda/metlink-wellington-homeassistant)

[*](https://icons8.com/icons/set/bus)![Bus](img/icons8-bus-48.png)   [*](https://icons8.com/icons/set/train)![Train](img/icons8-train-48.png)    [*](https://icons8.com/icons/set/water-transportation)![Ferry](img/icons8-water-transportation-48.png)  
  
  # **Metlink Wellington Home Assistant**
  
## **A Home Assistant transport sensor for the Wellington Regional Transport Network.** 

Metlink Wellington Home Assistant is a custom component for Home Assistant, that provides a transit sensor for a Metlink Wellington bus stop, train station, or ferry wharf. The sensor will give you the departure times or the mins until the next three departures from a given Metlink location for a selected route. Minutes are displayed when the departure is realtime, and times are displayed when a departure is scheduled but realtime information is not available because the service has not commenced from its starting location. 



check this - The sensor returns n/a if no stop departure is found.

## Show the RTI (real time info) expected arrival time of the next bus

![RTI](img/rti.png)
![Item info screenshot](img/info.png)

The [Metlink](https://www.metlink.org.nz/) website can help you to determine the exact stop and route to enter in the configuration.

### Configuration:

Then add the data to your configuration.yaml file as shown in the example:

Example configuration.yaml entry

sensor:
  - platform: metlink
    stop_number: a stop number or station/wharf id
    router_number: a router number or route id



### Configuration Variables:

stop_number:  string  Required

The start bus stop, train station, or ferry wharf.

router_number:  string  Required

The route id for the service.

### Configuration Examples:

A full configuration example could look like this:

This is Willis street Grand Arcade (stop 5008). Three routes that stop at this location have been configured.  

```
sensor:
  - platform: metlink
    stop_number: 5008
    route_number: 11
  - platform: metlink
    stop_number: 5008
    route_number: 43
  - platform: metlink
    stop_number: 5008
    route_number: 91
```


## Credit

Based on the research of @reedwade https://github.com/reedwade/metlink-api-maybe and initial code of @Br3nda https://github.com/Br3nda/metlink-wellington-homeassistant. 
