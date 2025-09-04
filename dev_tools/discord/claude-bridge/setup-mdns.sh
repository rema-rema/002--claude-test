#!/bin/bash

# mDNS alias configuration script
# This creates an alias for myapp.local without changing the system hostname

echo "Setting up mDNS alias for myapp.local..."

# Create avahi alias service file
cat > /tmp/myapp.service <<EOF
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>myapp</name>
  <service>
    <type>_http._tcp</type>
    <port>3000</port>
    <txt-record>Frontend Application</txt-record>
  </service>
  <service>
    <type>_http._tcp</type>
    <port>8000</port>
    <txt-record>Backend API</txt-record>
  </service>
</service-group>
EOF

echo "Service file created at /tmp/myapp.service"
echo ""
echo "To complete setup, run:"
echo "sudo cp /tmp/myapp.service /etc/avahi/services/"
echo "sudo systemctl restart avahi-daemon"
echo ""
echo "After setup, you can access:"
echo "- Frontend: http://ubuntu.local:3000"
echo "- Backend: http://ubuntu.local:8000"
echo ""
echo "Note: Custom hostname aliasing requires additional configuration."
echo "For now, use ubuntu.local or the IP address."