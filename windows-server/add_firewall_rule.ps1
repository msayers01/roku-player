# Allow the Roku LAN Media server through Windows Firewall for the local subnet only.
# Run once from an elevated PowerShell:  powershell -ExecutionPolicy Bypass -File add_firewall_rule.ps1
# Never forward this port on your router.
param([int]$Port = 8080)

$name = "Roku LAN Media ($Port)"
Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $name -Direction Inbound -Protocol TCP -LocalPort $Port `
    -RemoteAddress LocalSubnet -Profile Private -Action Allow | Out-Null
Write-Host "Firewall rule '$name' added (TCP $Port, local subnet, Private networks only)."
