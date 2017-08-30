# -*- coding:utf-8 -*-

import os
import time
import requests
#import json
from requests.compat import json
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from mijnpon.legacy_application_jwt import LegacyApplicationClientJWT
import urllib.parse

BASE_URL = 'https://api3.fleetwin.net/mob/1.0/'
TOKEN_URL = 'https://api3.fleetwin.net/sec/1.0/issue/oauth2/token'
REFRESH_URL = TOKEN_URL
SCOPE = ['https://api3.fleetwin.net/mob/1.0']


class Vehicle(object):
    def __init__(self, vehicleId, mijnpon_api, local_time=False):
        self._mijnpon_api = mijnpon_api
        self.vehicleId = vehicleId;
        self._local_time = local_time
#        self._vehicle = self._mijnpon_api.vehicle(self.vehicleId)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._repr_name)

    @property
    def _vehicle(self):
        return self._mijnpon_api._vehicle(self.vehicleId)
        # self._vehicle.get('Id')

    @property
    def id(self):
        return self.vehicleId
        # self._vehicle.get('Id')

    @property
    def license_plate(self):
        return self._vehicle.get('LicensePlate')

    @property
    def mileage(self):
        return self._vehicle.get('Mileage')

    @property
    def fuelremainder(self):
      return self._mijnpon_api._fuelremainder(self.vehicleId)

    @property
    def fuel_left(self):
      return self.fuelremainder.get('FuelLeft')

    @property
    def mileage_left(self):
      return self.fuelremainder.get('MileageLeft')

    @property
    def measureddata(self):
      return self._mijnpon_api._measureddata(self.vehicleId)

    @property
    def _repr_name(self):
        return self.license_plate


class Driver(object):
    def __init__(self, driver, mijnpon_api, local_time=False):
        self._mijnpon_api = mijnpon_api
        self._local_time = local_time
        self._driver = driver

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._repr_name)

    @property
    def id(self):
        return self._driver.get('Id')

    @property
    def first_name(self):
        return self._driver.get('FirstName')

    @property
    def sur_name(self):
        return self._driver.get('SurName')

    @property
    def _repr_name(self):
        return self.first_name + ' ' + self.sur_name


class Position(object):
    def __init__(self, mijnpon_api, local_time=False):
        self._mijnpon_api = mijnpon_api
        self._local_time = local_time

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._repr_name)

    @property
    def _position(self):
        return self._mijnpon_api._lastknownposition

    @property
    def address(self):
        return self._position.get('Address')

    @property
    def street(self):
        return self.address.get('Street')

    @property
    def postal_code(self):
        return self.address.get('PostalCode')

    @property
    def city(self):
        return self.address.get('City')

    @property
    def state(self):
        return self.address.get('State')

    @property
    def country(self):
        return self.address.get('Country')

    @property
    def reverse_geocoding_status(self):
        return self.address.get('ReverseGeocodingStatus')

    @property
    def _result(self):
        return self._position.get('Result')

    @property
    def coordinate(self):
        return self._result.get('Coordinate')

    @property
    def latitude(self):
        return self.coordinate.get('Latitude')

    @property
    def longitude(self):
        return self.coordinate.get('Longitude')

    @property
    def _repr_name(self):
        return self.street + ' ' + self.city


class MijnPon(object):
    def __init__(self, client_id='f5qbSDVQSyBnHv4cuDvQKImli0H6nvhsR3HJ066+HYA=', client_secret='CjAL01lJ/7XktXUUl2j+1E6iwEbjXB7PqoqkM1kstUw=', username, password, cache_ttl=270,
                 user_agent='iOS10.3.3 (Apple iPhone),app3.0.1,pon',
                 token=None, token_cache_file=None,
                 local_time=False):
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password
        self._token = token
        self._token_cache_file = token_cache_file
        self._cache_ttl = cache_ttl
        self._cache = {}
        self._local_time = local_time
        self._user_agent = user_agent

        self._auth()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def _token_saver(self, token):
        self._token = token
        if self._token_cache_file is not None:
                with os.fdopen(os.open(self._token_cache_file,
                                       os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600),
                               'w') as f:
                    json.dump(token, f)

    @property
    def token(self):
        self._token
    
    @property
    def authorized(self):
        self._mijnPonApi.authorized

    def _auth(self):
            self._mijnPonApi = OAuth2Session(client=LegacyApplicationClientJWT(client_id=self._client_id), scope=SCOPE, auto_refresh_url=REFRESH_URL, token_updater=self._token_saver)
            token = self._mijnPonApi.fetch_token(token_url=TOKEN_URL, username='pon\\'+self._username, password=self._password, client_id=self._client_id, client_secret=self._client_secret, scope=SCOPE)
            self._token_saver(token)

    def _get(self, endpoint, **params):
        query_string = urllib.parse.urlencode(params)
        url = BASE_URL + endpoint + '?' + query_string
        try:
          response = self._mijnPonApi.get(url)
          response.raise_for_status()
          return response.json()
        except TokenExpiredError:
          token = self._mijnPonApi.refresh_token(REFRESH_URL)
          self._token_saver(token)
          self._get(endpoint, params)

    def _post(self, endpoint, data, **params):
        query_string = urllib.parse.urlencode(params)
        url = BASE_URL + endpoint + '?' + query_string
        response = self._mijnPonApi.post(url, json=data, client_id=self._client_id,
                                       client_secret=self._client_secret)
        response.raise_for_status()
        return response.status_code

    def _checkCache(self, cache_key):
        if cache_key in self._cache:
            cache = self._cache[cache_key]
        else:
            cache = (None, 0)

        return cache

    def _bust_cache_all(self):
        self._cache = {}

    def _bust_cache(self, cache_key):
        self._cache[cache_key] = (None, 0)

    def _location(self, locationId):
        for location in self._locations:
            if location['locationID'] == locationId:
                return location

    @property
    def _vehicles(self):
        cache_key = 'vehicles'
        value, last_update = self._checkCache(cache_key)
        now = time.time()

        if not value or now - last_update > self._cache_ttl:
            value = self._get('vehicles')
            self._cache[cache_key] = (value, now)

        return value.get('Result')

    def _vehicle(self, vehicleId):
        for vehicle in self._vehicles:
            if vehicle.get('Id') == vehicleId:
                return vehicle

    @property
    def _drivers(self):
        cache_key = 'drivers'
        value, last_update = self._checkCache(cache_key)
        now = time.time()

        if not value or now - last_update > self._cache_ttl:
            value = self._get('drivers')
            self._cache[cache_key] = (value, now)

        return value.get('Result')

    @property
    def _lastknownposition(self):
        cache_key = 'lastknownposition'
        value, last_update = self._checkCache(cache_key)
        now = time.time()

        if not value or now - last_update > self._cache_ttl:
            value = self._get('drivers/currentdriver/lastknownposition')
            self._cache[cache_key] = (value, now)

        return value

    def _fuelremainder(self, vehicleId):
        cache_key = 'fuelremainder-%s' % vehicleId
        value, last_update = self._checkCache(cache_key)
        now = time.time()

        if not value or now - last_update > self._cache_ttl:
            value = self._get('driveassist/fuelremainder/%s' % vehicleId)
            self._cache[cache_key] = (value, now)

        return value.get('Result')

    def _measureddata(self, vehicleId):
        cache_key = 'measureddata-%s' % vehicleId
        dict, last_update = self._checkCache(cache_key)
        now = time.time()

        if not dict or now - last_update > self._cache_ttl:
            value = self._get('can/measureddata/latest/%s' % vehicleId)
            dict = {}
            for data in value.get('Result'):
                dict[data['SignalName']] = data

            self._cache[cache_key] = (dict, now)

        return dict

    @property
    def drivers(self):
        return [Driver(driver, self, self._local_time)
                for driver in self._drivers]

    @property
    def lastknownposition(self):
        return Position(self, self._local_time)

    @property
    def vehicles(self):
        return [Vehicle(vehicle.get('Id'), self, self._local_time)
                for vehicle in self._vehicles]
