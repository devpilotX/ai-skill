# Web vitals

Thresholds from [web.dev, Web Vitals](https://web.dev/articles/vitals). A page passes a metric when the
75th percentile of page loads from real users, split by mobile and desktop, is in the good range.

- Largest Contentful Paint (LCP): good at 2.5 s or less, poor above 4 s.
- Interaction to Next Paint (INP): good at 200 ms or less, poor above 500 ms. INP replaced First Input Delay as a Core Web Vital in March 2024.
- Cumulative Layout Shift (CLS): good at 0.1 or less, poor above 0.25.

Google revises these metrics. Check the page above before quoting a threshold in a report.

## Field and lab

Field data comes from real users: the Chrome User Experience Report (visible in PageSpeed Insights and
Search Console) or your own real user monitoring, for example with the web-vitals JavaScript library from Google
sending values to your analytics. Field data decides whether the page passes.

Lab data comes from a controlled run: Lighthouse, or the DevTools performance panel. It is repeatable
and good for debugging and for catching regressions in CI. It does not decide the pass. Lighthouse
cannot measure INP because it does not interact with the page, so it reports Total Blocking Time as a
lab proxy. A green Lighthouse score with poor field INP is common and means the lab run is not
exercising real interactions or real devices.

When reporting a number, name its source (field or lab), the device class, and the percentile.

## What moves each metric

LCP. Find the LCP element first. Then: make it discoverable in the initial HTML instead of injected by
script, preload it or set `fetchpriority="high"` if it is an image, serve it at display size in a modern
format, cut server response time, remove render blocking CSS and scripts, and do not lazy load it.

INP. Break long tasks on the main thread, yield between chunks of work, reduce hydration cost, move
non urgent work out of event handlers, avoid large synchronous re-renders on input, and keep third party
scripts in check. Use the DevTools performance panel with CPU throttling to find the slow interaction.

CLS. Set width and height, or the CSS aspect-ratio property, on images and video, reserve space for ads, embeds and late
content, avoid inserting content above existing content except in response to user input, and control
web font swap with the font-display descriptor and matched fallback metrics.
