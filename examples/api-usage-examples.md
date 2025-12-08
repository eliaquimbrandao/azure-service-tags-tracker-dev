# Azure Service Tags & IP Ranges Tracker - API Usage Examples

## 🎯 Overview

This document shows how to use the Azure Service Tags & IP Ranges Tracker as a public API to monitor specific services and detect changes.

## 📡 Base URL

Base path: [`https://eliaquimbrandao.github.io/azure-service-tags-tracker`](https://eliaquimbrandao.github.io/azure-service-tags-tracker)

- HTTPS only, no auth required.
- CORS is enabled, so you can call the endpoints directly from browser code or static sites.

## 📁 Available API Endpoints

| Endpoint | Description | Typical payload | Notes |
| --- | --- | --- | --- |
| `/data/current.json` | Latest Microsoft raw Service Tags feed | 4–6 MB | Mirrors Microsoft structure; good for one-off spot checks |
| `/data/summary.json` | Tracker statistics and available dates | <100 KB | Fast metadata lookup for automation |
| `/data/history/YYYY-MM-DD.json` | Daily raw snapshot | 4–6 MB | Compare adjacent days for accurate diffing |
| `/data/changes/latest-changes.json` | Most recent computed diff | 50–200 KB | Aggregated results from last run |
| `/data/changes/YYYY-MM-DD-changes.json` | Diffs for a specific date | 50–200 KB | Deterministic auditing for past runs |
| `/data/changes/manifest.json` | Index of all change files with sizes | <50 KB | Helpful for building download queues |

> ⏱️ GitHub Pages typically responds within 150–250 ms; downloading an entire historical snapshot over broadband takes ~0.5 s.

## 🧩 Use Directly from Your Pages

Because everything is static JSON, you can fetch data straight from the dashboard site without standing up a proxy. Example browser snippet:

```javascript
const BASE_URL = 'https://eliaquimbrandao.github.io/azure-service-tags-tracker';

async function loadLatestChanges() {
    const resp = await fetch(`${BASE_URL}/data/changes/latest-changes.json`, {
        headers: { 'Accept': 'application/json' }
    });
    if (!resp.ok) throw new Error('Failed to fetch change feed');
    return resp.json();
}

loadLatestChanges()
    .then(data => console.log('Latest change window:', data.timestamp))
    .catch(console.error);
```

Pair the call with `summary.json` to know which historical files exist before kicking off larger downloads.

### Key Fields in Data

```json
{
  "changeNumber": "123",
  "cloud": "Public",
  "values": [
    {
      "name": "Storage",
      "id": "Storage",
      "properties": {
        "changeNumber": "123",
        "region": "",
        "regionId": 0,
        "platform": "Azure",
        "systemService": "AzureStorage",
        "addressPrefixes": ["40.79.152.0/21", "..."]
      }
    }
  ]
}
```

## ⚠️ Important: Two Detection Methods

### Method 1: Pre-Computed Change Reports (Fast)

- **Endpoint**: `/data/changes/latest-changes.json` or `/data/changes/YYYY-MM-DD-changes.json`
- **Pros**: Fast queries, no processing needed
- **Cons**: Only shows changes detected during script execution, may show "+0/-0" metadata changes

### Method 2: Historical Snapshot Comparison (Accurate) ⭐ RECOMMENDED

- **Endpoint**: `/data/history/YYYY-MM-DD.json` (compare two snapshots)
- **Pros**: 100% accurate, compares actual IP lists, catches all real changes
- **Cons**: Requires fetching and comparing JSON files

**💡 Recommendation**: Use **Method 2** for production monitoring to ensure you catch all IP changes.

---

### Payload & Performance Tips

- `summary.json`, `manifest.json`, and `latest-changes.json` remain under 200 KB, so fetch them frequently to detect fresh data without worrying about bandwidth.
- Historical snapshots (`/data/history/...`) mirror Microsoft's large JSON. Retrieve only the days you truly need and reuse locally cached copies to avoid repeatedly downloading 5–6 MB files.
- Respect GitHub Pages caching: send `If-None-Match` headers or reuse the CDN-provided ETag to skip downloads when nothing changed.
- When scripting from CI or Functions, parallelize at most 2–3 downloads at a time—this keeps response latency predictable (~0.5 s per snapshot on broadband).

---

## ⚡ Quick Start (curl + jq)

Need a fast manual audit? The snippet below grabs the newest change report and prints services that added/removed IPs.

```bash
BASE="https://eliaquimbrandao.github.io/azure-service-tags-tracker"
LATEST_FILE=$(curl -s "$BASE/data/changes/manifest.json" \
    | jq -r '.files | max_by(.date).filename')

echo "Latest change file: $LATEST_FILE"
curl -s "$BASE/data/changes/$LATEST_FILE" \
    | jq -r '.changes[] | select((.added|length)+(.removed|length) > 0) |
            "\(.service) → +\(.added|length) / -\(.removed|length)"' |
    head -n 20
```

Sample output:

```text
Latest change file: 2025-12-08-changes.json
AzureCloud.eastus → +6 / -0
AzureMonitor → +2 / -1
AzureKeyVault → +0 / -4
...
```

Use the filename to fetch the full JSON or plug the service into the dashboard for detailed IPs.

---

## 🔧 Complete Implementation Examples

### PowerShell Example - Auto-Discovery

This function automatically discovers all available dates and checks for changes:

```powershell
function Test-AzureServiceChanges {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ServiceName
    )
    
    $baseUrl = "https://eliaquimbrandao.github.io/azure-service-tags-tracker"
    
    Write-Host "`n🔍 Checking if '$ServiceName' had ANY changes in collected history..." -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
    
    try {
        # Get list of all available historical snapshots
        $historyFiles = @()
        
        # Try method 1: Get from summary.json (if available)
        try {
            $summary = Invoke-RestMethod -Uri "$baseUrl/data/summary.json" -ErrorAction SilentlyContinue
            if ($summary.available_dates) {
                $historyFiles = $summary.available_dates | Sort-Object
            }
        } catch {
            # Fallback if available_dates field doesn't exist yet
        }
        
        # Method 2: Get from manifest.json (fallback)
        if ($historyFiles.Count -eq 0) {
            $manifest = Invoke-RestMethod -Uri "$baseUrl/data/changes/manifest.json"
            $manifestDates = @($manifest.files | ForEach-Object { $_.date })
            # Only use dates that actually exist in manifest - don't add current date
            $historyFiles = @($manifestDates) | Select-Object -Unique | Sort-Object
        }
        
        if ($historyFiles.Count -lt 2) {
            Write-Host "❌ Not enough historical data (need at least 2 snapshots)" -ForegroundColor Red
            return
        }
        
        Write-Host "📅 Found $($historyFiles.Count) historical snapshots" -ForegroundColor Gray
        Write-Host "   Dates: $($historyFiles -join ', ')`n" -ForegroundColor Gray
        
        $changesFound = @()
        
        # Compare each consecutive pair of dates
        for ($i = 0; $i -lt $historyFiles.Count - 1; $i++) {
            $date1 = $historyFiles[$i]
            $date2 = $historyFiles[$i + 1]
            
            Write-Host "🔄 Comparing $date1 → $date2..." -ForegroundColor DarkGray
            
            # Fetch both snapshots (with error handling)
            try {
                $snapshot1 = Invoke-RestMethod -Uri "$baseUrl/data/history/$date1.json" -ErrorAction Stop
                $snapshot2 = Invoke-RestMethod -Uri "$baseUrl/data/history/$date2.json" -ErrorAction Stop
            }
            catch {
                Write-Host "   ⚠️  Snapshot not found (skipping $date2)" -ForegroundColor Yellow
                continue
            }
            
            # Find services matching the name pattern
            $services1 = @($snapshot1.values | Where-Object { $_.name -like "*$ServiceName*" })
            
            foreach ($service1 in $services1) {
                $service2 = $snapshot2.values | Where-Object { $_.name -eq $service1.name } | Select-Object -First 1
                if (-not $service2) { continue }
                
                # Compare IP address prefixes
                $ips1 = @($service1.properties.addressPrefixes)
                $ips2 = @($service2.properties.addressPrefixes)
                
                $added = @($ips2 | Where-Object { $_ -notin $ips1 })
                $removed = @($ips1 | Where-Object { $_ -notin $ips2 })
                
                if ($added.Count -gt 0 -or $removed.Count -gt 0) {
                    $changesFound += [PSCustomObject]@{
                        Service = $service1.name
                        FromDate = $date1
                        ToDate = $date2
                        AddedIPs = $added.Count
                        RemovedIPs = $removed.Count
                    }
                }
            }
        }
        
        # Display results
        if ($changesFound.Count -gt 0) {
            Write-Host "✅ YES - Changes detected for '$ServiceName'!" -ForegroundColor Green
            Write-Host "`n📊 Summary:" -ForegroundColor Cyan
            
            foreach ($change in $changesFound) {
                Write-Host "`n   📌 $($change.Service)" -ForegroundColor White
                Write-Host "      Period: $($change.FromDate) → $($change.ToDate)" -ForegroundColor Gray
                Write-Host "      Changes: +$($change.AddedIPs) / -$($change.RemovedIPs) IPs" -ForegroundColor Yellow
            }
            
            Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
            Write-Host "📈 Total change events: $($changesFound.Count)" -ForegroundColor Cyan
            Write-Host "`n💡 To view detailed IP lists, visit:" -ForegroundColor White
            Write-Host "   $baseUrl" -ForegroundColor Blue
        } else {
            Write-Host "⚪ NO - No changes detected for '$ServiceName'" -ForegroundColor Gray
            Write-Host "   Service remained stable across all historical snapshots" -ForegroundColor DarkGray
        }
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Usage Examples
Test-AzureServiceChanges -ServiceName "Storage"
Test-AzureServiceChanges -ServiceName "AzureCloud.eastus"
Test-AzureServiceChanges -ServiceName "AzureKeyVault"
```

**Example Output:**

```text
🔍 Checking if 'Storage' had ANY changes in collected history...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Found 2 historical snapshots
   Dates: 2025-10-08, 2025-10-10

🔄 Comparing 2025-10-08 → 2025-10-10...
✅ YES - Changes detected for 'Storage'!

📊 Summary:

   📌 Storage
      Period: 2025-10-08 → 2025-10-10
      Changes: +5 / -2 IPs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Total change events: 1

💡 To view detailed IP lists, visit:
    https://eliaquimbrandao.github.io/azure-service-tags-tracker
```

---

### Python Example - Auto-Discovery

```python
import requests
from typing import List, Dict

def test_azure_service_changes(service_name: str) -> None:
    """Check if a service had ANY changes across all historical data."""
    
    base_url = 'https://eliaquimbrandao.github.io/azure-service-tags-tracker'
    
    print(f"\n🔍 Checking if '{service_name}' had ANY changes in collected history...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    try:
        # Get list of available historical snapshots
        dates = []
        
        # Try method 1: Get from summary.json (if available)
        try:
            summary = requests.get(f'{base_url}/data/summary.json').json()
            if 'available_dates' in summary:
                dates = sorted(summary['available_dates'])
        except:
            # Fallback if available_dates field doesn't exist yet
            pass
        
        # Method 2: Get from manifest.json (fallback)
        if not dates:
            manifest = requests.get(f'{base_url}/data/changes/manifest.json').json()
            manifest_dates = [f['date'] for f in manifest['files']]
            # Only use dates that actually exist in manifest - don't add current date
            dates = sorted(set(manifest_dates))
        
        if len(dates) < 2:
            print("❌ Not enough historical data (need at least 2 snapshots)")
            return
        
        print(f"📅 Found {len(dates)} historical snapshots")
        print(f"   Dates: {', '.join(dates)}\n")
        
        changes_found = []
        
        # Compare each consecutive pair of dates
        for i in range(len(dates) - 1):
            date1 = dates[i]
            date2 = dates[i + 1]
            
            print(f"🔄 Comparing {date1} → {date2}...")
            
            # Fetch both snapshots (with error handling)
            try:
                snapshot1 = requests.get(f'{base_url}/data/history/{date1}.json').json()
                snapshot2 = requests.get(f'{base_url}/data/history/{date2}.json').json()
            except:
                print(f"   ⚠️  Snapshot not found (skipping {date2})")
                continue
            
            # Find services matching the name pattern
            services1 = [
                s for s in snapshot1['values']
                if service_name.lower() in s['name'].lower()
            ]
            
            for service1 in services1:
                service2 = next(
                    (s for s in snapshot2['values'] if s['name'] == service1['name']),
                    None
                )
                if not service2:
                    continue
                
                # Compare IP addresses
                ips1 = set(service1['properties']['addressPrefixes'])
                ips2 = set(service2['properties']['addressPrefixes'])
                
                added = ips2 - ips1
                removed = ips1 - ips2
                
                if added or removed:
                    changes_found.append({
                        'service': service1['name'],
                        'from_date': date1,
                        'to_date': date2,
                        'added_ips': len(added),
                        'removed_ips': len(removed)
                    })
        
        # Display results
        if changes_found:
            print(f"✅ YES - Changes detected for '{service_name}'!")
            print("\n📊 Summary:")
            
            for change in changes_found:
                print(f"\n   📌 {change['service']}")
                print(f"      Period: {change['from_date']} → {change['to_date']}")
                print(f"      Changes: +{change['added_ips']} / -{change['removed_ips']} IPs")
            
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📈 Total change events: {len(changes_found)}")
            print(f"\n💡 To view detailed IP lists, visit:")
            print(f"   {base_url}")
        else:
            print(f"⚪ NO - No changes detected for '{service_name}'")
            print("   Service remained stable across all historical snapshots")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


# Usage Examples
if __name__ == "__main__":
    test_azure_service_changes('Storage')
    test_azure_service_changes('AzureCloud.eastus')
    test_azure_service_changes('AzureKeyVault')
```

---

## 🌐 Integration Guide for Other Languages

### Key Concepts for Any Language

#### Step 1: Auto-Discover Available Dates

```text
GET /data/summary.json
→ Extract: summary.available_dates[]
→ Fallback: GET /data/changes/manifest.json → Extract: files[].date
→ Sort dates chronologically
```

#### Step 2: Fetch Historical Snapshots

```text
For each consecutive date pair (date1, date2):
    GET /data/history/{date1}.json
    GET /data/history/{date2}.json
```

#### Step 3: Compare IP Address Lists

```text
For each service matching your search:
    ips1 = snapshot1.values[].properties.addressPrefixes
    ips2 = snapshot2.values[].properties.addressPrefixes
  
    added_ips = ips2 - ips1 (set difference)
    removed_ips = ips1 - ips2 (set difference)
  
    If added_ips OR removed_ips:
        → Record change event
```

#### Step 4: Display Results

```text
Output: Service name, date range, +/- IP counts
Link to dashboard for detailed IP lists
```

### Quick Start for Popular Languages

#### JavaScript / Node.js

```javascript
// Use fetch() or axios for HTTP requests
const response = await fetch(`${baseUrl}/data/summary.json`);
const summary = await response.json();
const dates = summary.available_dates.sort();

// Compare arrays
const added = ips2.filter(ip => !ips1.includes(ip));
const removed = ips1.filter(ip => !ips2.includes(ip));
```

#### C# / .NET

```csharp
// Use HttpClient for requests
using var client = new HttpClient();
var json = await client.GetStringAsync($"{baseUrl}/data/summary.json");
var summary = JsonSerializer.Deserialize<Summary>(json);
var dates = summary.AvailableDates.OrderBy(d => d);

// Compare lists with LINQ
var added = ips2.Except(ips1);
var removed = ips1.Except(ips2);
```

#### Go

```go
// Use net/http for requests
resp, _ := http.Get(baseUrl + "/data/summary.json")
var summary Summary
json.NewDecoder(resp.Body).Decode(&summary)
sort.Strings(summary.AvailableDates)

// Compare slices (use maps for efficiency)
addedMap := make(map[string]bool)
for _, ip := range ips2 {
    if !contains(ips1, ip) {
        addedMap[ip] = true
    }
}
```

#### Java

```java
// Use HttpClient or OkHttp for requests
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create(baseUrl + "/data/summary.json"))
    .build();
String json = client.send(request, BodyHandlers.ofString()).body();

// Compare lists
List<String> added = new ArrayList<>(ips2);
added.removeAll(ips1);
List<String> removed = new ArrayList<>(ips1);
removed.removeAll(ips2);
```

#### Ruby

```ruby
# Use net/http or httparty gem
require 'net/http'
require 'json'

uri = URI("#{base_url}/data/summary.json")
response = Net::HTTP.get(uri)
summary = JSON.parse(response)
dates = summary['available_dates'].sort

# Compare arrays
added = ips2 - ips1
removed = ips1 - ips2
```

---

## 📋 API Data Structure Reference

### summary.json

```json
{
  "last_updated": "2025-10-14T10:00:00Z",
  "total_services": 3039,
  "total_regions": 65,
  "available_dates": ["2025-10-08", "2025-10-10", "2025-10-13"],
  "changes_this_week": 5,
  "top_active_services": ["Storage", "AzureCloud.eastus"]
}
```

### history/YYYY-MM-DD.json (Snapshot)

```json
{
  "changeNumber": "123",
  "cloud": "Public",
  "values": [
    {
      "name": "Storage",
      "id": "Storage",
      "properties": {
        "changeNumber": "123",
        "region": "",
        "platform": "Azure",
        "systemService": "AzureStorage",
        "addressPrefixes": ["40.79.152.0/21", "52.239.128.0/17"]
      }
    }
  ]
}
```

### changes/manifest.json

```json
{
  "files": [
    {
      "date": "2025-10-08",
      "filename": "2025-10-08-changes.json",
      "total_changes": 15
    }
  ]
}
```

---

## 🎯 Common Use Cases

### 1. Monitor Specific Service for Any Changes

**Goal**: Alert if "Storage" service IPs change at all  
**Method**: Run auto-discovery function weekly, check for changes_found > 0

### 2. Track Regional Service Changes

**Goal**: Monitor "AzureCloud.eastus" for regional updates  
**Method**: Search for services containing "eastus", compare all snapshots

### 3. Security Compliance Monitoring

**Goal**: Validate firewall rules stay current with Azure IP ranges  
**Method**: Compare latest snapshot with your firewall configuration, alert on diffs

### 4. Historical Change Analysis

**Goal**: See when "AzureKeyVault" last changed  
**Method**: Iterate through all date pairs, find most recent change event

---

## 💡 Best Practices

1. **Cache Historical Data**: Download snapshots once, compare locally to reduce API calls
2. **Error Handling**: Always handle 404 errors (snapshots may not exist for all dates)
3. **Rate Limiting**: No rate limits currently, but be respectful with bulk requests
4. **Date Validation**: Don't add current date to history list (snapshot may not exist yet)
5. **Set Operations**: Use set operations (Except, intersect) for efficient IP comparison
6. **Logging**: Log change events for audit trails and compliance reporting

---

## 🔗 Additional Resources

- **Live Dashboard**: <https://eliaquimbrandao.github.io/azure-service-tags-tracker>
- **GitHub Repository**: <https://github.com/eliaquimbrandao/azure-service-tags-tracker>
- **Microsoft Documentation**: [Azure Service Tags Overview](https://learn.microsoft.com/azure/virtual-network/service-tags-overview)

---

## 📞 Support

For issues, feature requests, or contributions, please visit the [GitHub Issues page](https://github.com/eliaquimbrandao/azure-service-tags-tracker/issues).
