# ❓ Frequently Asked Questions

Jump to: [General](#general) · [YouTube & cookies](#youtube--cookies) · [Downloads & formats](#downloads--formats) · [Installation](#installation) · [Docker](#docker) · [AWS & deployment](#aws--deployment) · [Errors](#errors) · [Development](#development)

---

## General

<details><summary><b>1. What is Universal Video Downloader?</b></summary>
A self-hosted web app that downloads video/audio from hundreds of sites using yt-dlp, with a modern UI, live progress, history, and a cookie-auth pipeline.
</details>

<details><summary><b>2. Is it free?</b></summary>
Yes — open-source under the MIT license.
</details>

<details><summary><b>3. Is it legal?</b></summary>
The tool itself is legal. How you use it must comply with copyright law and each platform's Terms of Service in your jurisdiction. You are responsible for your usage.
</details>

<details><summary><b>4. Does it work offline?</b></summary>
The UI loads locally, but downloading obviously needs internet access to the source sites.
</details>

<details><summary><b>5. Which platforms are supported?</b></summary>
YouTube, Rutube, Vimeo, Twitch, TikTok, X/Twitter, Facebook, Instagram, Dailymotion, Bilibili, SoundCloud, Reddit, VK, Threads, and <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">1000+ more</a> via yt-dlp.
</details>

<details><summary><b>6. Does it run on mobile?</b></summary>
The UI is fully responsive; you can use it from a phone browser pointed at your server.
</details>

<details><summary><b>7. What languages does the UI support?</b></summary>
English, Русский, and Հայերեն — switch instantly, no reload.
</details>

<details><summary><b>8. Can multiple people use one instance?</b></summary>
Yes, but there's no per-user auth yet (see the <a href="ROADMAP.md">roadmap</a>). Restrict access at the network/proxy level for now.
</details>

---

## YouTube & cookies

<details><summary><b>9. Why does YouTube say "Sign in to confirm you're not a bot"?</b></summary>
YouTube requires a logged-in session from many IPs. Upload cookies — see <a href="COOKIES.md">COOKIES.md</a>.
</details>

<details><summary><b>10. How do I get cookies?</b></summary>
Use the "Get cookies.txt LOCALLY" extension, export while logged in, and upload via Settings → Cookies.
</details>

<details><summary><b>11. Where do I put cookies.txt?</b></summary>
Upload via Settings, or place it at <code>./data/cookies.txt</code>.
</details>

<details><summary><b>12. My cookies stopped working.</b></summary>
Sessions expire — re-export fresh cookies.
</details>

<details><summary><b>13. Do cookies get committed to git?</b></summary>
No, they're gitignored and never logged.
</details>

<details><summary><b>14. Should I enable COOKIES_FROM_BROWSER on my server?</b></summary>
No — set it to <code>false</code> on headless servers (there's no browser). Use an uploaded cookies.txt.
</details>

<details><summary><b>15. Which browsers can cookies be read from automatically?</b></summary>
chrome, chromium, edge, firefox (configurable via <code>COOKIE_BROWSER_ORDER</code>).
</details>

<details><summary><b>16. Is it safe to use my main YouTube account?</b></summary>
It works, but a throwaway account reduces risk if the cookie file leaks.
</details>

---

## Downloads & formats

<details><summary><b>17. What video qualities can I choose?</b></summary>
best, 8K, 4K, 1440p, 1080p, 720p, 480p, 360p.
</details>

<details><summary><b>18. What video containers are supported?</b></summary>
MP4, MKV, WEBM, AVI, MOV.
</details>

<details><summary><b>19. Can I download audio only?</b></summary>
Yes — MP3, AAC, M4A, FLAC, WAV, OGG.
</details>

<details><summary><b>20. Where are files saved?</b></summary>
In <code>DOWNLOADS_DIR</code> (default <code>./backend/downloads</code>), or S3 if enabled.
</details>

<details><summary><b>21. Can I download playlists?</b></summary>
Not yet — it's on the roadmap. Currently one video per request.
</details>

<details><summary><b>22. Can I pause/resume downloads?</b></summary>
Yes, plus cancel and priority.
</details>

<details><summary><b>23. How many downloads run at once?</b></summary>
Controlled by <code>MAX_CONCURRENT_DOWNLOADS</code> (default 3).
</details>

<details><summary><b>24. What happens to duplicate requests?</b></summary>
Identical in-flight requests are coalesced into a single job.
</details>

<details><summary><b>25. Why is my estimated size slightly off?</b></summary>
Sizes are estimates from metadata/bitrate until the download completes.
</details>

<details><summary><b>26. Do subtitles download?</b></summary>
Not yet — planned.
</details>

---

## Installation

<details><summary><b>27. What Python version do I need?</b></summary>
Python 3.13+.
</details>

<details><summary><b>28. Do I need FFmpeg?</b></summary>
Yes — for merging and audio conversion. It's bundled in the Docker image.
</details>

<details><summary><b>29. How do I install FFmpeg?</b></summary>
apt/winget/brew — see <a href="INSTALL.md">INSTALL.md</a>.
</details>

<details><summary><b>30. How do I update yt-dlp?</b></summary>
<code>pip install -U yt-dlp</code> or rebuild the Docker image.
</details>

<details><summary><b>31. Activation fails on Windows PowerShell.</b></summary>
Run <code>Set-ExecutionPolicy -Scope CurrentUser RemoteSigned</code>.
</details>

---

## Docker

<details><summary><b>32. How do I start with Docker?</b></summary>
<code>docker compose up -d --build</code>.
</details>

<details><summary><b>33. How do I add Nginx?</b></summary>
<code>docker compose --profile proxy up -d</code>.
</details>

<details><summary><b>34. Where is data stored in Docker?</b></summary>
In the <code>./data</code>, <code>./backend/downloads</code>, and <code>./logs</code> volumes.
</details>

<details><summary><b>35. "No space left on device"?</b></summary>
<code>docker system prune -af</code> and use the multi-stage image.
</details>

---

## AWS & deployment

<details><summary><b>36. How do I deploy to AWS?</b></summary>
Use the Terraform in <code>terraform/</code> — see <a href="AWS.md">AWS.md</a>.
</details>

<details><summary><b>37. I can't reach my EC2 site on :8000.</b></summary>
Open inbound TCP 8000 in the Security Group.
</details>

<details><summary><b>38. My public IP changes on restart.</b></summary>
Attach an Elastic IP.
</details>

<details><summary><b>39. How do I add HTTPS?</b></summary>
Put Nginx in front and run Certbot — see <a href="DEPLOYMENT.md">DEPLOYMENT.md</a>.
</details>

<details><summary><b>40. Can I use S3 for storage?</b></summary>
Yes — set <code>S3_ENABLED=true</code> and configure the bucket (or use the IAM role).
</details>

---

## Errors

<details><summary><b>41. What does <code>video_unavailable</code> mean?</b></summary>
Private/deleted/404, or an outdated extractor (e.g. Rutube). Update yt-dlp.
</details>

<details><summary><b>42. What does <code>network_error</code> mean?</b></summary>
A timeout or connection problem. Check connectivity and retry.
</details>

<details><summary><b>43. Why don't I see raw yt-dlp errors?</b></summary>
By design — errors are translated into structured envelopes. Raw text is logged server-side only. See <a href="ERRORS.md">ERRORS.md</a>.
</details>

---

## Development

<details><summary><b>44. How do I run the tests?</b></summary>
<code>pytest --cov=backend</code>.
</details>

<details><summary><b>45. How do I lint?</b></summary>
<code>ruff check backend tests</code>.
</details>

<details><summary><b>46. How do I contribute?</b></summary>
See <a href="../CONTRIBUTING.md">CONTRIBUTING.md</a>.
</details>

<details><summary><b>47. Is there an API?</b></summary>
Yes — REST + WebSocket, documented at <code>/docs</code> and in <a href="API.md">API.md</a>.
</details>
