
"""
Metlink Wellington Custom Component for Home Assistant.

Support for Metlink's Wellington public transport using API.
Bus, Train, Ferry. Great Wellington / Whanganui a Tara.

Version: 1.0  (July 2020) - Initial Release

Author:  SmbKiwi.

Based on github.com/Br3nda/metlink-wellington-homeassistant
by Brenda Wallace.

"""

from datetime import timedelta, datetime
import logging

import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_STOP_URL,
    CONF_ROUTE_NUMBER,
    CONF_STOP_NUMBER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by metlink.org.nz"
ICONS = {
    "Train": "mdi:train",
    "Bus": "mdi:bus",
    "Ferry": "mdi:ferry",
    "Schoolbus": "mdi:bus",
    "n/a": "mdi:clock",
    "null": "mdi:clock",
    None: "mdi:clock",
}

SCAN_INTERVAL = timedelta(minutes=1)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ROUTE_NUMBER): cv.string,
        vol.Required(CONF_STOP_NUMBER): cv.string,
    }
)


def format_timestamp(t):
    """Create times that match those seen on the street signs."""
    ret = datetime.strptime(t[0:16], '%Y-%m-%dT%H:%M')
    delta = timedelta(hours=int(t[19:22]), minutes=int(t[23:]))
    if t[18] == '+':
        ret += delta
    elif t[18] == '-':
        ret -= delta

    return ret.strftime("%I:%M%p %a")


def setup_platform(hass, config, add_entities, discovery_info=None):

    """" Get the Metlink public transport sensor.
        journal contains [0] Station ID start, [1] Station ID destination
        [2] Station name start, and [3] Station name destination.
    """
    route_number = config[CONF_ROUTE_NUMBER]
    stop_number = config[CONF_STOP_NUMBER]
    add_entities([MetlinkSensor(stop_number, route_number)])


def service_summary(service):
    realtime = "(sched)"
    if service.is_real_time:
        realtime = "(real)"

    return "{} {} to {}".format(
        realtime,
        service.origin_stop_name,
        service.destination_stop_name,
    )


class MetlinkSensor(Entity):
    """Implementation of an Metlink public transport sensor."""

    def __init__(self, stop_number, route_number):
        """"Initialize the sensor."""
        self.stop_number = stop_number
        self.route_number = route_number
        self._name = 'stop_{stop_number}_route_{route_number}'.format(
            stop_number=stop_number,
            route_number=route_number
        )
        self._icon = ICONS[None]
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Route {}".format(self.route_number)

    @property
    def state(self):
        """"Return the state of the sensor."""
         #  return self.metlink_stop.services[0].departure_status.
        service = self.metlink_stop.next_service(
            route_number=self.route_number)
        if service and service.is_real_time:
            return int(service.departure_seconds / 60)
        elif service and service.display_departure:
            return format_timestamp(service.display_departure)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attributes = {
            'Stop': self.stop_number,
            'Route': self.route_number,
            'StopName': self.metlink_stop.stop_name,
            'Latitude': self.metlink_stop.latitude,
            'Longitude': self.metlink_stop.longitude,
            ATTR_ATTRIBUTION: ATTRIBUTION
        }

        if self.next_service:
            attributes.update(self.next_service.attributes())

        return attributes

    @property
    def next_service(self):
        return self.metlink_stop.next_service(route_number=self.route_number)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        if self.next_service and self.next_service.is_real_time:
            return "min"
        else:
            return "offline"

    def update(self):
        """Get the latest data from Metlink and update the states."""
        url = ATTR_STOP_URL.format(stop_number=self.stop_number)
        r = requests.get(url)
        self.metlink_stop = MetlinkStop(r.json())
        # get self.metlink_stop.services[0].service.mode
        current_service = self.metlink_stop.next_service(
            route_number=self.route_number)
        self._icon = ICONS[current_service.route_mode]


class MetlinkStop(object):
    """" A bus stop or train station """

    def __init__(self, data):
        self._data = data

    def services(self, route_number=None):
        for data in self._data.get('Services'):
            service = MetlinkService(data)
            if str(route_number) == str(service.route_number):
                yield service

    @property
    def stop_name(self):
        return self._data.get('Stop', {}).get('Name')

    @property
    def longitude(self):
        return self._data.get('Stop', {}).get('Long')

    @property
    def latitude(self):
        return self._data.get('Stop', {}).get('Lat')

    def next_service(self, route_number=None):
        """"The next service expected to arrive here,
        optionally filtered by route_number."""
        for service in self.services(route_number=route_number):
            return service


class MetlinkService(object):
    """A single service, e.g. Bus on route 1, from bus stop 1000,
    traveling the whole route."""

    def __init__(self, service_data):
        self._service_data = service_data

    @property
    def route_number(self):
        return self._get('ServiceID')

    @property
    def departure_status(self):
        return self._get('DepartureStatus')

    @property
    def display_departure(self):
        return self._get('DisplayDeparture')

    @property
    def is_real_time(self):
        return self._get('IsRealtime')

    @property
    def origin_stop_name(self):
        return self._get('OriginStopName')

    @property
    def destination_stop_name(self):
        return self._get('DestinationStopName')

    @property
    def departure_seconds(self):
        return self._get('DisplayDepartureSeconds')

    @property
    def expected_departure(self):
        value = self._get('ExpectedDeparture', False)
        if value:
            return format_timestamp(value)
        return value

    @property
    def route_name(self):
        return self._service_data.get('Service', {}).get('Name')
    
    @property
    def route_mode(self):
        return self._service_data.get('Service', {}).get('Mode')
    
    def attributes(self):
        return {
            'Operator': self._get('OperatorRef'),
            'ExpectedDeparture': self.expected_departure,
            'DepartureStatus': self._get('DepartureStatus'),
            'IsRealtime': self._get('IsRealtime'),
            'OriginStopName': self._get('OriginStopName'),
            'DestinationStopName': self._get('DestinationStopName'),
            'VehicleFeature': self._get('VehicleFeature'),
            'ServiceID': self._get('ServiceID'),
            'ServiceName': self.route_name,
            'ServiceMode': self.route_mode
        }

    def _get(self, key, value=None):
        return self._service_data.get(key, value)

    def __str__(self):
        return str(self._service_data)

