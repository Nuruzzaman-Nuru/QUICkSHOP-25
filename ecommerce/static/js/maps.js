function initMap() {
    const mapContainer = document.getElementById('map');
    const mapLoading = document.getElementById('mapLoading');
    const mapError = document.getElementById('mapError');

    if (!mapContainer) return;

    try {
        // Hide error message if it was previously shown
        mapError.style.display = 'none';
        
        // Create the map centered on the search location
        const map = new google.maps.Map(mapContainer, {
            zoom: 13,
            center: { 
                lat: searchLocation.lat,
                lng: searchLocation.lng 
            },
            mapTypeControl: false,
            fullscreenControl: false,
            streetViewControl: false,
            styles: [
                {
                    featureType: "poi",
                    elementType: "labels",
                    stylers: [{ visibility: "off" }]
                }
            ]
        });

        // Add a marker for the search location
        new google.maps.Marker({
            position: searchLocation,
            map: map,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: "#4285F4",
                fillOpacity: 0.5,
                strokeWeight: 2,
                strokeColor: "#1967D2"
            },
            title: "Your Location"
        });

        // Add markers for each shop
        shopLocations.forEach(shop => {
            const marker = new google.maps.Marker({
                position: { lat: shop.lat, lng: shop.lng },
                map: map,
                title: shop.name,
                animation: google.maps.Animation.DROP
            });

            // Create an info window for the shop
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div class="map-info-window">
                        <h6>${shop.name}</h6>
                        <div class="distance">${shop.distance} km away</div>
                        <a href="/shop/${shop.id}" class="btn btn-primary btn-sm">View Shop</a>
                    </div>
                `
            });

            // Add click listener to show info window
            marker.addListener('click', () => {
                infoWindow.open(map, marker);
            });
        });

        // Hide loading spinner
        if (mapLoading) {
            mapLoading.style.display = 'none';
        }
    } catch (error) {
        console.error('Error initializing map:', error);
        if (mapError) {
            mapError.style.display = 'block';
        }
        if (mapLoading) {
            mapLoading.style.display = 'none';
        }
    }
}

function initLocationInput() {
    const useLocationSwitch = document.getElementById('useLocation');
    const locationFields = document.getElementById('locationFields');
    const locationInput = document.getElementById('locationInput');
    const latInput = document.getElementById('lat');
    const lngInput = document.getElementById('lng');

    if (!useLocationSwitch || !locationFields) return;

    // Initialize Places Autocomplete
    const autocomplete = new google.maps.places.Autocomplete(locationInput, {
        types: ['geocode']
    });

    // Handle place selection
    autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry) {
            latInput.value = place.geometry.location.lat();
            lngInput.value = place.geometry.location.lng();
            document.getElementById('filterForm').submit();
        }
    });

    // Handle location switch toggle
    useLocationSwitch.addEventListener('change', () => {
        if (useLocationSwitch.checked) {
            locationFields.style.display = 'flex';
            // Try to get current location
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        latInput.value = position.coords.latitude;
                        lngInput.value = position.coords.longitude;
                        // Reverse geocode to show address
                        const geocoder = new google.maps.Geocoder();
                        geocoder.geocode({
                            location: {
                                lat: position.coords.latitude,
                                lng: position.coords.longitude
                            }
                        }, (results, status) => {
                            if (status === 'OK' && results[0]) {
                                locationInput.value = results[0].formatted_address;
                                document.getElementById('filterForm').submit();
                            }
                        });
                    },
                    (error) => {
                        console.error('Geolocation error:', error);
                        locationFields.style.display = 'flex';
                    }
                );
            }
        } else {
            locationFields.style.display = 'none';
            latInput.value = '';
            lngInput.value = '';
            locationInput.value = '';
            document.getElementById('filterForm').submit();
        }
    });
}