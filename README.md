# Burp WP a.k.a. WordPress Scanner

![Burp WP](images/logo.svg)

Find known vulnerabilities in WordPress plugins and themes using Burp Suite proxy.

**TL;DR: a [WPScan](https://wpscan.org/)-like plugin for [Burp](https://portswigger.net/).**

Originally created by [Kacper Szurek](https://security.szurek.pl/). This fork is
maintained by [SecurityShrimp](https://securityshrimp.com) and modernized for the
**WPScan Vulnerability Database API v3** and current Burp Suite releases (the legacy
Extender API now runs as a shim over the Montoya API).

> **You need a free WPScan API token.** Since the v3 migration, vulnerability data is
> fetched per plugin/theme from the API. Grab a token at
> [wpscan.com/api](https://wpscan.com/api/) and paste it into the **API Key** field on
> the extension tab.

# Usage
[Install](#installation) extension. Browse WordPress sites through Burp proxy. Vulnerable plugins and themes will appear on the issue list.

![Usage](images/usage.png)

If you have Burp Pro, issues will also appear inside *Scanner* tab. Interesting things will be highlighted.

![Usage pro](images/usage_pro.png)


# Table of contents

* [Usage](#usage)
* [Installation](#installation)
* [Issue type](#issue-type)
* [Options](#options)
* [Offline database](#offline-database)
* [Intruder payload generator](#intruder-payload-generator)
* [Detect plugins using wp-ajax.php](#detect-plugins-using-wp-ajaxphp)
* [License](#license)
* [Changelog](#changelog)

# Installation

WordPress Scanner is available inside [BApp Store](https://portswigger.net/bappstore).
  1. Inside Burp go to **Extensions->BApp Store**
  2. Choose WordPress Scanner

  ![WordPress Scanner](images/bapp_store_1.png)
  
  3. Click **Install button**

  ![WordPress Scanner Install](images/bapp_store_2.png)

You can also install Burp WP manually:

1. Download [Jython](http://www.jython.org/downloads.html) standalone JAR, for example version [2.7](http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.7.0/jython-standalone-2.7.0.jar)
2. Go to **Extensions->Extensions settings**. Set path inside `Location of Jython standalone JAR file`

![Install Jython](images/install_jython.png)

3. Download the [newest Burp WP](https://raw.githubusercontent.com/f8al/wordpress-scanner/master/burp_wp.py)
4. Go to **Extensions->Installed**. Click **Add**. Set `Extension type` to `Python`. Set path inside `Extension file`.

![Install Burp WP](images/install_burp_wp.png)

5. Burp WP should appear inside `Burp Extensions list`. Also you will see new tab.

![Installed extension](images/installed.png)

# Issue type

There are 3 types:

1. Default type (always enabled)
  ```
  {issue_type} inside {(plugin|theme)} {plugin_name} version {detected_version}
  ```

  It has `High severity`. If version is detected using `readme.txt`, `Certain confidence` is set. Otherwise we use `Firm confidence`.

2. Plugin vulnerabilities regarding detected version (option 4 enabled)
  ```
  Potential {issue_type} inside {(plugin|theme)} {plugin_name} fixed in {version_number}
  ```

  It has `Information severity` and `Certain confidence`.

3. Print info about discovered plugins (option 5 enabled)
  ```
  Found {(plugin|theme)} {plugin_name}
  ```

  or if plugin version is detected:

  ```
  Found {(plugin|theme)} {plugin_name} version {detected_version}
  ```

  It has `Information severity` and `Certain confidence` if is detected. Otherwise `Firm confidence` is used.

# Options

![Options](images/options.png)

1. Update button

  Downloads the extension database: the `admin-ajax.php` action map and the plugin/theme
  enumeration wordlists used by the Intruder generators. Files are served from this fork
  and verified with `sha512` before use, so an update only re-downloads what changed.

  Vulnerability data itself is **not** bundled — it is fetched on demand per plugin/theme
  from the [WPScan Vulnerability Database API v3](https://wpscan.com/api/) using your API token.

  This button also checks whether a new [Burp WP version exists](https://raw.githubusercontent.com/f8al/wordpress-scanner/master/version.sig) and offers a simple auto-update mechanism.

2. Use readme.txt for detecting plugins version

  Sometimes it's possible to detect plugin version through its resource because some of them have `?ver=` string.

  For example:

  ```
  http://www.example.com/wp-content/plugins/contact-form-7/includes/css/styles.css?ver=4.9.2
  ```

  Version can be checked using simple regular expression:

  ```
  re.compile("ver=([0-9\.]+)", re.IGNORECASE)
  ```

  But this approach is very *buggy*. Instead  more advanced heuristics are used.

  Most plugins contains `readme.txt` file:

  ```
  === Plugin Name ===
  Donate link: http://example.com/
  Stable tag: 4.3

  Here is a short description of the plugin.

  == Changelog ==

  = 1.0 =
  * A change since the previous version.
  ```

  So current plugin version can be obtained from `Stable tag` or `Changelog`.

  This idea is from [WPScan versionable.rb](https://github.com/wpscanteam/wpscan/blob/master/lib/common/models/wp_item/versionable.rb).

3. Scan full response body

  By default only request URL is used for finding plugins and themes.

  This works just fine but in some cases you may want to parse full response body. Use with caution as this might be slow.

4. Report all known vulnerabilities, even those already fixed in the detected version

  By default an issue is only added when a vulnerable plugin version is detected (`plugin_version < fixed_version`).

  If you want to report every known vulnerability for a detected plugin regardless of the installed version - use this option.

5. Report discovered plugins even if they have no known vulnerabilities

  Normally plugins/themes which are not vulnerable are ignored.

  If you want to have information about installed plugins on given website, even if they are not vulnerable - use this option.

6. Enable auto update

  Auto update database once per 24 h.

  It also checks if new Burp WP version exists.

7. Enable debug mode

  For development purpose.

  You can see output inside: **Extensions->Installed->Burp WP->Output tab**

  ![Debug mode](images/debug_mode.png)

8. What detect

  Decide if you want to search for vulnerable plugins, themes or both.

9. Custom wp-content

  Detection mechanism is based on `wp-content` string.

  But it can be [changed](https://codex.wordpress.org/Editing_wp-config.php#Moving_wp-content_folder) by website owner. Here you can customize this option.

10. Clear issues list button

  This button will remove all issues from issues list inside extension tab.

11. Force update button

  Similar to `Update button` but it downloads new database even if newest one is already installed.

12. Reset settings to default

  Restore extension state to factory defaults.

13. Discover plugins using admin-ajax.php
	See [Detect plugins using wp-ajax.php](#detect-plugins-using-wp-ajaxphp).

14. API Key

  Your [WPScan Vulnerability Database API](https://wpscan.com/api/) token. Required for
  vulnerability lookups. Click **Request API Key** to open the WPScan signup page.

# Offline database
  All vulnerabilities are provided by [WPScan](https://wpscan.org/) - see the [Vulnerability Database API](https://wpscan.com/api/).

  Burp WP supports offline mode.

  If you operate from high-security network without Internet access you can easily copy database file from normal Burp WP instance to your offline one.

  Then use `Choose file` option.

  If it's valid Burp WP database it will be imported automatically.

# Intruder payload generator
  Because only proxied requests and responses are inspected, passive scanning can't discover every plugin and theme installed on a site.

  You can enumerate them actively with the Intruder payload generators. Each generator sprays `/{wp-content}/{plugins|themes}/<slug>/` paths from a bundled wordlist; responses that don't 404 reveal installed plugins/themes, which the scanner then looks up against the WPScan API.

  The wordlists ship with the extension database (`data/plugins.json`, `data/themes.json`) and are refreshed by the **Update** button. They are generated from the public [WordPress.org plugin/theme API](https://api.wordpress.org/) (popularity-ordered) with `tools/generate_wordlists.py` — currently **~50,000 plugin** and **~8,000 theme** slugs. The **Themes** / **Plugins** counters on the extension tab show how many are loaded.

  Right click a URL inside **Proxy->HTTP history** and choose **Send to Burp WP Intruder**. ![Send to intruder](images/intruder_send.png)

  This replaces the request method with GET, removes all parameters, and sets the payload position marker.

  Now go to **Intruder->Tab X->Positions**. Correct the URL so it points to the WordPress homepage.

  ![Intruder positions](images/intruder_position.png)

  Inside the **Payloads** tab uncheck **Payload encoding** so `/` isn't converted to `%2f`.

  Then set **Payload type** to **Extension generated** and click **Select generator**:

  ![Intruder choose payload](images/intruder_choose_payload.png)

  There are 3 generators:
  1. WordPress Plugins
  2. WordPress Themes
  3. WordPress Plugins and Themes


  ![Intruder attack](images/intruder_attack.png)

# Detect plugins using wp-ajax.php
  This is new technique available since Burp WP 0.2.

  It discovers plugins based on calls to `wp-admin/admin-ajax.php` endpoint.

  Custom [action database](https://github.com/f8al/wordpress-scanner/blob/master/data/admin_ajax.json) is used for this.

  Basically when plugin send request to `/admin-ajax.php?action=akismet_recheck_queue` Burp WP makes reverse lookup in action database.

  ![Wp-ajax detection technique](images/wp_ajax.png)  

# License
  MIT License

  Copyright (c) 2018 Kacper Szurek

  Modernized 2026 by SecurityShrimp (WPScan API v3, current Burp / Montoya, restored
  Intruder wordlists).

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

  The WPScan data is licensed separately. Please find the WPScan license [here](https://raw.githubusercontent.com/wpscanteam/wpscan/master/LICENSE).

# Changelog

* 1.0 - First stable release of the modernized fork; documentation refresh.
* 0.9 - Settings UI wording fixes; attribution links repointed to the fork / SecurityShrimp.
* 0.8 - Restored the Intruder plugin & theme enumeration wordlists, now sourced from the WordPress.org API (~50k plugins / ~8k themes); added a UTF-8 source encoding declaration so Jython loads the extension.
* 0.7 - Fixed HTTP requests on current Burp (the legacy Extender API now shims the Montoya API): database updates and vulnerability lookups work again.
* 0.6 - Repointed auto-update and database downloads to the `f8al/wordpress-scanner` fork.
* 0.3-0.5 - Modernized for the WPScan Vulnerability Database API v3 (per-plugin/theme lookups; a free WPScan API token is now required).
* 0.2 - Add discovery plugins using `wp-ajax.php?action`
* 0.1.1 - Updates are downloaded through Burp proxy, fix clear list issues button, implement doPassiveScan function
* 0.1 - Beta version
