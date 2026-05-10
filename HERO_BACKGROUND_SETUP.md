# Hero Background Image Setup

## Implementation Complete ✅

The hero sections across all main pages have been updated to use a background image with the following specifications:

### Files Updated
- ✅ `index.html` - Homepage hero
- ✅ `services.html` - Services page hero
- ✅ `about.html` - About page hero  
- ✅ `contact.html` - Contact page hero
- ✅ `blog/index.html` - Blog index hero
- ✅ `css/style.css` - CSS styling for hero layout

### HTML Implementation

Each hero section now uses a `<picture>` element:

```html
<section class="hero">
  <picture>
    <source srcset="/images/nissan-patrol-y62-dubai-desert.avif" type="image/avif">
    <img src="/images/nissan-patrol-y62-dubai-desert.jpg" alt="White Nissan Patrol Y62 in Dubai desert">
  </picture>
  <div class="hero-content">
    <!-- H1, subtitle, CTAs left-aligned -->
  </div>
</section>
```

**Features:**
- AVIF format (modern, best compression) with JPG fallback
- Full alt text: "White Nissan Patrol Y62 in Dubai desert"
- Responsive `<picture>` element for optimal format delivery

### CSS Styling

**Layout Changes:**
- Hero height: `min-height: 90vh` (was 100vh)
- Content alignment: **LEFT-aligned** (was centered)
- Content positioning: `justify-content: flex-start` (was center)
- Text alignment: `text-align: left` (was center)
- Max-width: 600px for better readability
- Left margin: `var(--spacing-lg)` to offset from left edge

**Background & Overlay:**
- Picture element positioned absolutely, full-bleed
- `object-fit: cover` for proper image scaling
- Dark gradient overlay: `linear-gradient(135deg, rgba(10, 14, 26, 0.85) 0%, rgba(10, 14, 26, 0.55) 100%)`
- Gradient darker on mobile: `rgba(10, 14, 26, 0.92) → rgba(10, 14, 26, 0.75)`

**Responsive Behavior:**
- Desktop: Overlay lighter on right side (where car is) so photo visible
- Mobile: Overlay darker overall (85-92%) to ensure text readability over car image
- CTA buttons left-aligned on all screen sizes

### Image Requirements

You need to add these files to `/images/`:

**Primary (Required):**
- `nissan-patrol-y62-dubai-desert.avif` - 90vh hero height
- `nissan-patrol-y62-dubai-desert.jpg` - Fallback for older browsers

**Specifications:**
- Recommended width: 1600px+ (for desktop)
- Aspect ratio: 16:9 or similar (covers 90vh)
- Content layout: White Patrol car on RIGHT side, empty desert on LEFT side
- The LEFT side (where H1 sits) should be mostly clear/light for contrast
- Quality: Compressed to < 300KB for AVIF, < 400KB for JPG

**Image Tips:**
- Shoot/source Patrol against Dubai desert background
- Ensure left 40% of image is mostly empty sky/sand (for H1 readability)
- Lighting: Golden hour or bright daylight (high contrast with dark overlay)
- Use tool like Squoosh (https://squoosh.app) to convert JPG → AVIF

### Browser Compatibility

- **Modern browsers**: Will load AVIF (better compression)
- **Older browsers**: Will load JPG fallback
- **Safari < 16**: Uses JPG
- **Firefox**: Uses AVIF (if updated)
- **Chrome 85+**: Uses AVIF

### Zero JavaScript Required

The hero layout is 100% CSS. No JavaScript needed for image loading or responsive behavior.

### Styling Details

**Hero Section CSS Classes:**
```css
.hero {
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: flex-start;  /* Left-aligned */
  text-align: left;
}

.hero picture {
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.hero::before {
  /* Dark overlay gradient */
  background: linear-gradient(135deg, rgba(10, 14, 26, 0.85) 0%, rgba(10, 14, 26, 0.55) 100%);
  z-index: 1;
}

.hero-content {
  max-width: 600px;
  position: relative;
  z-index: 2;
  margin-left: var(--spacing-lg);  /* Left padding */
}

.hero-cta {
  justify-content: flex-start;  /* Buttons left-aligned */
}
```

### Testing

After adding the image files, test:
1. **Desktop**: Verify H1 sits over left (empty) area, car visible on right
2. **Mobile**: Verify text readable (darker overlay kicks in)
3. **Format fallback**: Disable AVIF in DevTools → should load JPG
4. **Performance**: Check image loads under 1s (use WebPageTest)

### Next Steps

1. Add `nissan-patrol-y62-dubai-desert.avif` and `.jpg` to `/images/`
2. Test on multiple devices (desktop, tablet, mobile)
3. Verify AVIF loads first (DevTools Network tab)
4. Check lighthouse score (should remain 90+)

---

**Note:** Blog post pages do NOT have hero sections (they start with `<article>` element), so only the 5 main pages + CSS were updated.

