netsh advfirewall firewall add rule name="VoiceAI-Web" dir=in action=allow protocol=tcp localport=5173
netsh advfirewall firewall add rule name="VoiceAI-LK-TCP" dir=in action=allow protocol=tcp localport=7880,7881
netsh advfirewall firewall add rule name="VoiceAI-LK-UDP" dir=in action=allow protocol=udp localport=50000-50020
netsh advfirewall firewall add rule name="VoiceAI-Token" dir=in action=allow protocol=tcp localport=8082
