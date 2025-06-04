"""
Location utility module for the Enhanced Attendance System.

This module provides location validation and distance calculation functionality.
"""

import logging
from typing import Tuple
from geopy.distance import geodesic

from ..core.config import Config

logger = logging.getLogger(__name__)


class LocationValidator:
    """
    Location validation class for attendance system.
    
    Handles distance calculation and office proximity validation.
    """
    
    def __init__(self):
        """Initialize location validator with office coordinates."""
        self.office_lat = Config.OFFICE_LATITUDE
        self.office_lon = Config.OFFICE_LONGITUDE
        self.office_radius = Config.OFFICE_RADIUS
        self.office_coords = (self.office_lat, self.office_lon)
    
    def calculate_distance(self, latitude: float, longitude: float) -> float:
        """
        Calculate distance from office in meters.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Distance in meters
        """
        try:
            user_coords = (latitude, longitude)
            distance = geodesic(self.office_coords, user_coords).meters
            return distance
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')  # Return infinite distance on error
    
    def is_within_office_radius(self, latitude: float, longitude: float) -> Tuple[bool, float]:
        """
        Check if location is within office radius.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Tuple of (is_within_radius, distance_in_meters)
        """
        distance = self.calculate_distance(latitude, longitude)
        is_within = distance <= self.office_radius
        
        logger.debug(f"Location check: {latitude}, {longitude} - Distance: {distance:.2f}m, Within radius: {is_within}")
        
        return is_within, distance
    
    def get_location_summary(self, latitude: float, longitude: float) -> dict:
        """
        Get comprehensive location summary.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Dictionary with location analysis
        """
        distance = self.calculate_distance(latitude, longitude)
        is_within = distance <= self.office_radius
        
        return {
            'latitude': latitude,
            'longitude': longitude,
            'distance_meters': distance,
            'distance_formatted': f"{distance:.0f}m",
            'is_within_radius': is_within,
            'office_radius': self.office_radius,
            'office_coords': self.office_coords,
            'status': 'valid' if is_within else 'outside_radius'
        }


# Backward compatibility function
def is_within_radius(user_lat: float, user_lon: float, 
                    office_lat: float, office_lon: float, 
                    radius_meters: int) -> Tuple[bool, float]:
    """
    Legacy function for backward compatibility.
    
    Args:
        user_lat: User latitude
        user_lon: User longitude
        office_lat: Office latitude
        office_lon: Office longitude
        radius_meters: Radius in meters
        
    Returns:
        Tuple of (is_within_radius, distance_in_meters)
    """
    try:
        user_coords = (user_lat, user_lon)
        office_coords = (office_lat, office_lon)
        distance = geodesic(office_coords, user_coords).meters
        return distance <= radius_meters, distance
    except Exception as e:
        logger.error(f"Error in legacy location check: {e}")
        return False, float('inf') 