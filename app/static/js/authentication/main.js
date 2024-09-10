

// Getting Client Ip Address
document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.getElementById('hamburger-menu');
    const navMenu = document.getElementById('nav-menu');

    hamburger.addEventListener('click', () => {
      navMenu.classList.toggle('active');
    });
  });


  function getLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(sendPosition);
    } else {
      alert("Geolocation is not supported by this browser.");
    }
  }

  function sendPosition(position) {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;

    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10`)
      .then(response => response.json())
      .then(data => {
        const city = data.address.city || data.address.town || data.address.village;
        const country = data.address.country;

        document.getElementById('city').value = city;
        document.getElementById('country').value = country;
      })
      .catch(error => console.error('Error:', error));
  }

  window.onload = getLocation;