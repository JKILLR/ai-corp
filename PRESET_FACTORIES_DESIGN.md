# AI Corp Factory Presets Design

## Overview

This document defines two industry-specific presets that leverage AI Corp's integration system to create automated production pipelines:

1. **Content Factory** - Automated content generation and multi-platform publishing
2. **iOS App Factory** - AI-powered iOS app development pipeline

Both presets follow the n8n-inspired plug-and-play integration model, where connectors snap into agent workflows as simple steps.

---

## Design Principles

### 1. Plug-and-Play Simplicity
Connectors should be as easy to attach as n8n nodes:
```yaml
steps:
  - id: generate_script
    type: integration
    connector: openai
    action: generate_text
    params:
      model: gpt-4o
      prompt: "{{input.topic}}"
```

### 2. Visual Pipeline Thinking
Workflows are designed as visual pipelines that can be rendered in the Web UI:
```
[Trigger] → [Process] → [Transform] → [Gate] → [Publish]
```

### 3. Template Reusability
Common patterns are extracted as reusable molecule templates that can be customized.

### 4. Quality Gates as Checkpoints
Human approval points are built into workflows at critical junctures.

---

# Part 1: Content Factory Preset

## Vision

An AI-powered content production studio that:
- Clones and adapts viral content
- Generates original content with AI avatars
- Publishes to 9+ platforms simultaneously
- Tracks performance and optimizes

**Target Users:** Content creators, agencies, faceless YouTube channels, AI influencer operators

## Use Cases

1. **Faceless YouTube Automation** - Generate educational/entertainment videos without showing face
2. **AI Influencer** - Create consistent AI persona content across platforms
3. **Content Repurposing** - Transform long-form content into shorts, clips, posts
4. **Product Content at Scale** - Generate variations of product videos/images

---

## Required Connectors (P1)

| Connector | Purpose | Auth Type |
|-----------|---------|-----------|
| OpenAI | Script generation, analysis | API Key |
| Cloudinary | Media storage, transformation | API Key |
| Telegram | Notifications, triggers | Bot Token |

## Optional Connectors (P2+)

### AI & Generation
| Connector | Purpose | Priority |
|-----------|---------|----------|
| Anthropic | Alternative LLM | P2 |
| ElevenLabs | Voice synthesis | P2 |
| HeyGen | Avatar video generation | P2 |
| Runway | AI video generation | P3 |
| Midjourney | Image generation | P3 |
| Sora | Text-to-video | P3 |

### Research & Data
| Connector | Purpose | Priority |
|-----------|---------|----------|
| Perplexity | Trend research | P2 |
| Google Sheets | Data storage, tracking | P2 |
| Airtable | Content database | P2 |
| RapidAPI | TikTok/IG scraping | P2 |

### Publishing Platforms
| Connector | Purpose | Priority |
|-----------|---------|----------|
| YouTube | Long-form, Shorts | P1 |
| Instagram | Reels, Posts, Stories | P2 |
| TikTok | Short videos | P2 |
| Twitter/X | Threads, posts | P2 |
| LinkedIn | Professional content | P3 |
| Facebook | Videos, posts | P3 |
| Threads | Text posts | P3 |
| Pinterest | Pins | P3 |
| Bluesky | Posts | P3 |

---

## Organizational Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         CEO (Human)                              │
│                    Strategic direction                           │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         COO (Claude)                             │
│          Content strategy, workflow orchestration                │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
│   IDEATION    │       │  PRODUCTION   │       │  PUBLISHING   │
│   DEPARTMENT  │       │  DEPARTMENT   │       │  DEPARTMENT   │
├───────────────┤       ├───────────────┤       ├───────────────┤
│ • Research    │       │ • Video Prod  │       │ • Platform    │
│ • Scripting   │       │ • Audio Prod  │       │   Management  │
│ • Trend       │       │ • Image/      │       │ • Scheduling  │
│   Analysis    │       │   Thumbnail   │       │ • Analytics   │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Departments

#### 1. Ideation Department
**Focus:** Content ideas, scripts, research

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| Research Director | Trend analysis, competitor monitoring | Perplexity, RapidAPI |
| Script Writer | Generate scripts from research | OpenAI, Anthropic |
| Content Strategist | Content calendar, topic selection | Airtable, Sheets |

#### 2. Production Department
**Focus:** Create media assets

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| Video Producer | Avatar videos, edits | HeyGen, Runway, Sora |
| Audio Producer | Voiceovers, music | ElevenLabs |
| Visual Designer | Thumbnails, graphics | OpenAI (DALL-E), Midjourney |

#### 3. Publishing Department
**Focus:** Multi-platform distribution

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| Platform Manager | Platform-specific optimization | All social connectors |
| Scheduler | Optimal timing, queue management | Airtable |
| Analytics Specialist | Performance tracking | Platform analytics APIs |

---

## Workflow Templates (Molecules)

### Molecule 1: Viral Clone Pipeline

Based on the n8n workflow pattern from the screenshots.

```yaml
molecule:
  id: viral-clone
  name: "Viral Content Clone"
  description: "Clone and adapt viral content from TikTok/Reels"

  trigger:
    type: integration
    connector: telegram
    action: receive_message
    filter: "contains(message, 'clone:')"

  steps:
    # STEP 1: Download & Analyze
    - id: extract_url
      type: transform
      action: extract_url
      input: "{{trigger.message}}"

    - id: download_video
      type: integration
      connector: rapidapi
      action: download_tiktok
      params:
        url: "{{extract_url.url}}"

    - id: extract_thumbnail
      type: integration
      connector: rapidapi
      action: extract_thumbnail
      params:
        video: "{{download_video.file}}"

    - id: upload_to_storage
      type: integration
      connector: cloudinary
      action: upload
      params:
        file_path: "{{download_video.file}}"
        folder: "viral-clones/{{date}}"

    - id: analyze_thumbnail
      type: integration
      connector: openai
      action: analyze_image
      params:
        image_url: "{{extract_thumbnail.url}}"
        prompt: "Analyze this thumbnail. What makes it click-worthy?"

    - id: transcribe_audio
      type: integration
      connector: openai
      action: transcribe
      params:
        file_path: "{{download_video.audio}}"

    - id: generate_script
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Original transcript: {{transcribe_audio.text}}
          Thumbnail analysis: {{analyze_thumbnail.data}}

          Create a unique script inspired by this viral video.
          Make it original but capture what made the original engaging.

    - id: save_to_sheets
      type: integration
      connector: google_sheets
      action: append_row
      params:
        spreadsheet_id: "{{config.tracking_sheet}}"
        values:
          - "{{date}}"
          - "{{extract_url.url}}"
          - "{{generate_script.data}}"
          - "pending"

    # GATE: Human approval before production
    - id: content_approval
      type: gate
      gate_id: content-review
      criteria:
        - "Script is original (not plagiarized)"
        - "Aligns with brand voice"
        - "No policy violations"
      on_approve: continue
      on_reject: notify_and_stop

    # STEP 2: Notify ready for production
    - id: notify_ready
      type: integration
      connector: telegram
      action: send_message
      params:
        text: |
          ✅ Viral clone ready for production

          Original: {{extract_url.url}}
          Script: {{generate_script.data | truncate(200)}}

          Reply "produce" to continue
```

### Molecule 2: Avatar Video Production

```yaml
molecule:
  id: avatar-video
  name: "AI Avatar Video"
  description: "Generate video with AI avatar from script"

  input:
    script: string
    avatar_id: string
    voice_id: string

  steps:
    - id: split_sections
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Split this script into sections for video:
          {{input.script}}

          Output JSON with sections array.

    - id: generate_voice
      type: integration
      connector: elevenlabs
      action: text_to_speech
      params:
        text: "{{input.script}}"
        voice_id: "{{input.voice_id}}"

    - id: create_avatar_video
      type: integration
      connector: heygen
      action: create_video
      params:
        avatar_id: "{{input.avatar_id}}"
        audio_url: "{{generate_voice.url}}"
        script: "{{input.script}}"

    - id: wait_for_render
      type: poll
      connector: heygen
      action: get_video_status
      params:
        video_id: "{{create_avatar_video.video_id}}"
      until: "status == 'completed'"
      interval: 30
      timeout: 600

    - id: download_video
      type: integration
      connector: heygen
      action: download_video
      params:
        video_id: "{{create_avatar_video.video_id}}"

    - id: upload_final
      type: integration
      connector: cloudinary
      action: upload
      params:
        file_path: "{{download_video.file}}"
        folder: "avatar-videos/{{date}}"

    - id: generate_thumbnail
      type: integration
      connector: openai
      action: generate_image
      params:
        prompt: |
          YouTube thumbnail for video about: {{input.script | summarize}}
          Style: Bold text, bright colors, expressive face

    # GATE: Quality check before publishing
    - id: quality_review
      type: gate
      gate_id: production-review
      criteria:
        - "Video renders correctly"
        - "Audio syncs with avatar"
        - "Thumbnail is click-worthy"

  output:
    video_url: "{{upload_final.url}}"
    thumbnail_url: "{{generate_thumbnail.data[0]}}"
```

### Molecule 3: Multi-Platform Publish

```yaml
molecule:
  id: multi-platform-publish
  name: "9-Platform Publisher"
  description: "Publish content to all social platforms"

  input:
    video_url: string
    thumbnail_url: string
    title: string
    description: string
    tags: array
    platforms: array  # Optional: subset of platforms

  steps:
    # Generate platform-specific variations
    - id: generate_variations
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Create platform-specific versions of this content:

          Title: {{input.title}}
          Description: {{input.description}}

          Generate JSON with:
          - youtube: {title, description, tags}
          - tiktok: {caption with hashtags}
          - instagram: {caption, hashtags}
          - twitter: {thread array, max 280 chars each}
          - linkedin: {professional post}
          - facebook: {post}
          - threads: {post}
          - pinterest: {pin_title, pin_description}
          - bluesky: {post}

    # Parallel publishing to all platforms
    - id: publish_youtube
      type: integration
      connector: youtube
      action: upload_video
      params:
        file_url: "{{input.video_url}}"
        title: "{{generate_variations.youtube.title}}"
        description: "{{generate_variations.youtube.description}}"
        tags: "{{generate_variations.youtube.tags}}"
        thumbnail_url: "{{input.thumbnail_url}}"
        privacy: "public"
      condition: "platforms.includes('youtube') or platforms.empty()"
      parallel: true

    - id: publish_tiktok
      type: integration
      connector: tiktok
      action: upload_video
      params:
        file_url: "{{input.video_url}}"
        caption: "{{generate_variations.tiktok.caption}}"
      condition: "platforms.includes('tiktok') or platforms.empty()"
      parallel: true

    - id: publish_instagram
      type: integration
      connector: instagram
      action: upload_reel
      params:
        file_url: "{{input.video_url}}"
        caption: "{{generate_variations.instagram.caption}}"
      condition: "platforms.includes('instagram') or platforms.empty()"
      parallel: true

    - id: publish_twitter
      type: integration
      connector: twitter
      action: post_thread
      params:
        tweets: "{{generate_variations.twitter.thread}}"
        media_url: "{{input.video_url}}"
      condition: "platforms.includes('twitter') or platforms.empty()"
      parallel: true

    - id: publish_linkedin
      type: integration
      connector: linkedin
      action: post_video
      params:
        video_url: "{{input.video_url}}"
        text: "{{generate_variations.linkedin.post}}"
      condition: "platforms.includes('linkedin') or platforms.empty()"
      parallel: true

    - id: publish_facebook
      type: integration
      connector: facebook
      action: post_video
      params:
        video_url: "{{input.video_url}}"
        message: "{{generate_variations.facebook.post}}"
      condition: "platforms.includes('facebook') or platforms.empty()"
      parallel: true

    - id: publish_threads
      type: integration
      connector: threads
      action: post
      params:
        text: "{{generate_variations.threads.post}}"
      condition: "platforms.includes('threads') or platforms.empty()"
      parallel: true

    - id: publish_pinterest
      type: integration
      connector: pinterest
      action: create_pin
      params:
        media_url: "{{input.thumbnail_url}}"
        title: "{{generate_variations.pinterest.pin_title}}"
        description: "{{generate_variations.pinterest.pin_description}}"
        link: "{{publish_youtube.url}}"
      condition: "platforms.includes('pinterest') or platforms.empty()"
      parallel: true

    - id: publish_bluesky
      type: integration
      connector: bluesky
      action: post
      params:
        text: "{{generate_variations.bluesky.post}}"
      condition: "platforms.includes('bluesky') or platforms.empty()"
      parallel: true

    # Aggregate results and notify
    - id: aggregate_results
      type: transform
      action: collect
      inputs:
        - publish_youtube
        - publish_tiktok
        - publish_instagram
        - publish_twitter
        - publish_linkedin
        - publish_facebook
        - publish_threads
        - publish_pinterest
        - publish_bluesky

    - id: save_to_tracker
      type: integration
      connector: airtable
      action: create_record
      params:
        table: "Published Content"
        fields:
          title: "{{input.title}}"
          date: "{{now}}"
          platforms: "{{aggregate_results.successful}}"
          youtube_url: "{{publish_youtube.url}}"
          tiktok_url: "{{publish_tiktok.url}}"
          instagram_url: "{{publish_instagram.url}}"

    - id: notify_complete
      type: integration
      connector: telegram
      action: send_message
      params:
        text: |
          🚀 Published to {{aggregate_results.successful | length}} platforms!

          {{#each aggregate_results.successful}}
          ✅ {{this.platform}}: {{this.url}}
          {{/each}}

          {{#if aggregate_results.failed}}
          ❌ Failed:
          {{#each aggregate_results.failed}}
          - {{this.platform}}: {{this.error}}
          {{/each}}
          {{/if}}
```

### Molecule 4: AI Creatives Factory

Based on the Nano Banana workflow from the screenshots.

```yaml
molecule:
  id: ai-creatives-factory
  name: "AI Product Creatives"
  description: "Generate multiple creative variations for products"

  trigger:
    type: integration
    connector: airtable
    action: on_record_created
    params:
      table: "Product Catalog"

  steps:
    - id: get_product_data
      type: integration
      connector: airtable
      action: get_record
      params:
        record_id: "{{trigger.record_id}}"

    - id: generate_angles
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Product: {{get_product_data.name}}
          Description: {{get_product_data.description}}
          Target Audience: {{get_product_data.audience}}

          Generate 5 different creative angles for this product:
          1. Problem/Solution angle
          2. Lifestyle angle
          3. Social proof angle
          4. Urgency angle
          5. Feature highlight angle

          For each, provide:
          - Headline (max 10 words)
          - Body copy (max 50 words)
          - Visual description
          - CTA

    - id: generate_images
      type: loop
      items: "{{generate_angles.angles}}"
      step:
        type: integration
        connector: openai
        action: generate_image
        params:
          prompt: "{{item.visual_description}}, product photography, professional, {{get_product_data.style}}"
          size: "1024x1024"
          n: 3  # 3 variations per angle

    - id: upload_all_images
      type: integration
      connector: cloudinary
      action: upload_batch
      params:
        files: "{{generate_images.results | flatten}}"
        folder: "creatives/{{get_product_data.id}}"
        transformations:
          - { width: 1080, height: 1080, crop: "fill" }  # Instagram
          - { width: 1200, height: 628, crop: "fill" }   # Facebook
          - { width: 1080, height: 1920, crop: "fill" }  # Stories

    - id: create_variations_records
      type: integration
      connector: airtable
      action: create_records
      params:
        table: "Creative Variations"
        records: "{{upload_all_images.results | map_to_records}}"

    - id: notify_complete
      type: integration
      connector: telegram
      action: send_message
      params:
        text: |
          🎨 Generated {{generate_images.results | length}} creatives for {{get_product_data.name}}

          View in Airtable: {{config.airtable_view_url}}
```

---

## Quality Gates

### Gate 1: Content Review
**Checkpoint:** Before production begins
```yaml
gate:
  id: content-review
  name: "Content Review"
  criteria:
    - id: originality
      name: "Content is original"
      description: "Not directly copied, sufficiently transformed"
      required: true
    - id: brand_voice
      name: "Matches brand voice"
      description: "Tone and style align with brand guidelines"
      required: true
    - id: policy_check
      name: "No policy violations"
      description: "Complies with platform policies"
      required: true
    - id: quality_bar
      name: "Meets quality bar"
      description: "Script is engaging and well-structured"
      required: false
```

### Gate 2: Production Review
**Checkpoint:** Before publishing
```yaml
gate:
  id: production-review
  name: "Production Review"
  criteria:
    - id: video_quality
      name: "Video quality acceptable"
      required: true
    - id: audio_sync
      name: "Audio syncs correctly"
      required: true
    - id: thumbnail_ctr
      name: "Thumbnail is click-worthy"
      required: true
    - id: captions
      name: "Captions are accurate"
      required: false
```

---

## Configuration

### preset.yaml
```yaml
preset:
  id: content-factory
  name: "AI Content Factory"
  version: "1.0.0"
  description: "Automated content generation and multi-platform publishing"

  complexity: 4

  team_size:
    min: 5
    max: 30
    default: 12

  required_integrations:
    - openai
    - cloudinary
    - telegram

  recommended_integrations:
    - youtube
    - elevenlabs
    - heygen
    - airtable

  departments:
    - ideation
    - production
    - publishing

  molecule_templates:
    - viral-clone
    - avatar-video
    - multi-platform-publish
    - ai-creatives-factory

  customization:
    required:
      - identity.name
      - identity.brand_voice
    optional:
      - publishing.default_platforms
      - publishing.schedule_timezone
      - content.default_language
      - avatar.default_id
      - voice.default_id
```

---

# Part 2: iOS App Factory Preset

## Vision

An AI-powered iOS app development studio that:
- Generates app concepts and designs
- Produces Swift/SwiftUI code
- Automates build and testing
- Handles App Store submission

**Target Users:** Solo developers, indie studios, rapid prototypers, agencies

## Use Cases

1. **Rapid MVP Development** - Go from idea to App Store in days
2. **App Cloning** - Study and recreate successful app patterns
3. **Client Projects** - Agency handling multiple app projects
4. **Continuous Updates** - Automated feature development and releases

---

## Required Connectors (P1)

| Connector | Purpose | Auth Type |
|-----------|---------|-----------|
| OpenAI | Code generation, analysis | API Key |
| GitHub | Code repository | OAuth |
| Cloudinary | Asset storage | API Key |

## Optional Connectors (P2+)

### Design
| Connector | Purpose | Priority |
|-----------|---------|----------|
| Figma | UI/UX designs, export | OAuth |
| Midjourney | App icons, graphics | API Key |
| DALL-E (OpenAI) | Quick graphics | API Key |
| Lottie/Rive | Animations | API Key |

### Development
| Connector | Purpose | Priority |
|-----------|---------|----------|
| Anthropic | Alternative code gen | API Key |
| Cursor API | Code assistance | API Key |
| Xcode Cloud | CI/CD | Apple ID |
| Fastlane | Build automation | Local |

### Testing
| Connector | Purpose | Priority |
|-----------|---------|----------|
| TestFlight | Beta distribution | Apple ID |
| BrowserStack | Device testing | API Key |
| Appetize | Simulator preview | API Key |

### Deployment
| Connector | Purpose | Priority |
|-----------|---------|----------|
| App Store Connect | Submission | Apple ID |
| RevenueCat | Subscriptions/IAP | API Key |
| Firebase | Auth, analytics, push | Google OAuth |

### Backend Services
| Connector | Purpose | Priority |
|-----------|---------|----------|
| Supabase | Database, auth | API Key |
| Firebase | Full backend | Google OAuth |
| Cloudflare Workers | Serverless functions | API Key |

### Project Management
| Connector | Purpose | Priority |
|-----------|---------|----------|
| Linear | Task tracking | OAuth |
| Notion | Specs, docs | OAuth |
| Airtable | Project database | API Key |

---

## Organizational Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         CEO (Human)                              │
│                 Product vision, final approval                   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         COO (Claude)                             │
│            Project management, sprint planning                   │
└─────────────────────────────────────────────────────────────────┘
                                │
    ┌───────────────┬───────────┼───────────┬───────────────┐
    │               │           │           │               │
┌───▼───┐       ┌───▼───┐   ┌───▼───┐   ┌───▼───┐       ┌───▼───┐
│PRODUCT│       │DESIGN │   │DEVELOP│   │  QA   │       │RELEASE│
└───────┘       └───────┘   └───────┘   └───────┘       └───────┘
```

### Departments

#### 1. Product Department
**Focus:** Requirements, specs, user stories

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| Product Director | Requirements gathering, prioritization | Notion, Linear |
| UX Researcher | User flow, wireframes | Figma |

#### 2. Design Department
**Focus:** Visual design, assets

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| UI Designer | App screens, components | Figma |
| Asset Creator | Icons, graphics, animations | Midjourney, Lottie |
| Brand Designer | App icon, screenshots | DALL-E |

#### 3. Development Department
**Focus:** Code generation, implementation

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| iOS Architect | Architecture decisions, code review | GitHub, OpenAI |
| Swift Developer | Feature implementation | OpenAI, Anthropic |
| Backend Developer | API, database | Supabase, Firebase |

#### 4. QA Department
**Focus:** Testing, quality assurance

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| QA Lead | Test strategy, automation | Xcode, BrowserStack |
| Test Engineer | Manual & automated testing | TestFlight |

#### 5. Release Department
**Focus:** Build, deploy, publish

| Role | Responsibilities | Connectors Used |
|------|-----------------|-----------------|
| Release Manager | App Store submission | App Store Connect |
| DevOps Engineer | CI/CD, builds | Xcode Cloud, Fastlane |

---

## Workflow Templates (Molecules)

### Molecule 1: App Concept Generation

```yaml
molecule:
  id: app-concept
  name: "App Concept Generator"
  description: "Generate app concept from idea"

  input:
    idea: string
    target_audience: string
    monetization: string

  steps:
    - id: market_research
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Research the market for this app idea:
          Idea: {{input.idea}}
          Target: {{input.target_audience}}

          Provide:
          1. Similar apps in the market
          2. Gaps and opportunities
          3. Unique value proposition
          4. Potential challenges

    - id: generate_prd
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Create a Product Requirements Document:

          Idea: {{input.idea}}
          Market Research: {{market_research.data}}
          Monetization: {{input.monetization}}

          Include:
          - App name suggestions (5 options)
          - One-line description
          - Core features (MVP)
          - User stories
          - Technical requirements
          - Success metrics

    - id: generate_wireframes
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Design wireframe descriptions for key screens:
          PRD: {{generate_prd.data}}

          For each screen describe:
          - Layout
          - Key elements
          - User interactions
          - Navigation

    - id: create_figma_frames
      type: integration
      connector: figma
      action: create_file
      params:
        name: "{{input.idea | slugify}}-wireframes"
        content: "{{generate_wireframes.data}}"

    - id: save_to_notion
      type: integration
      connector: notion
      action: create_page
      params:
        database_id: "{{config.projects_db}}"
        properties:
          name: "{{generate_prd.app_name}}"
          status: "Concept"
          prd: "{{generate_prd.data}}"
          figma_url: "{{create_figma_frames.url}}"

    # GATE: Concept approval
    - id: concept_approval
      type: gate
      gate_id: concept-review
      criteria:
        - "Idea is feasible"
        - "Market opportunity exists"
        - "Scope is appropriate for MVP"
```

### Molecule 2: UI Design Generation

```yaml
molecule:
  id: ui-design
  name: "UI Design Generator"
  description: "Generate UI designs from wireframes"

  input:
    figma_file_id: string
    style_guide: object

  steps:
    - id: get_wireframes
      type: integration
      connector: figma
      action: get_file
      params:
        file_id: "{{input.figma_file_id}}"

    - id: generate_design_specs
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Create detailed UI design specifications:

          Wireframes: {{get_wireframes.frames | describe}}
          Style Guide: {{input.style_guide}}

          For each screen:
          - Color palette usage
          - Typography
          - Spacing and layout
          - Component specifications
          - Micro-interactions

    - id: generate_app_icon
      type: integration
      connector: openai
      action: generate_image
      params:
        prompt: |
          iOS app icon for: {{input.app_name}}
          Style: Modern, clean, iOS 17 style
          {{input.style_guide.icon_description}}
        size: "1024x1024"
        n: 5

    - id: generate_screenshots
      type: integration
      connector: openai
      action: generate_image
      params:
        prompt: |
          App Store screenshot mockup for screen: {{item.name}}
          Description: {{item.design_spec}}
          Device: iPhone 15 Pro
        size: "1290x2796"
      loop: "{{generate_design_specs.screens}}"

    - id: upload_assets
      type: integration
      connector: cloudinary
      action: upload_batch
      params:
        files:
          - "{{generate_app_icon.images}}"
          - "{{generate_screenshots.images}}"
        folder: "apps/{{input.app_id}}/assets"

    # GATE: Design approval
    - id: design_approval
      type: gate
      gate_id: design-review
      criteria:
        - "Designs match brand guidelines"
        - "All screens are complete"
        - "Assets meet App Store requirements"
```

### Molecule 3: Swift Code Generation

```yaml
molecule:
  id: swift-codegen
  name: "Swift Code Generator"
  description: "Generate SwiftUI code from designs"

  input:
    figma_file_id: string
    architecture: string  # MVVM, TCA, etc.

  steps:
    - id: extract_components
      type: integration
      connector: figma
      action: get_components
      params:
        file_id: "{{input.figma_file_id}}"

    - id: generate_models
      type: integration
      connector: openai
      action: generate_text
      params:
        model: "gpt-4o"
        prompt: |
          Generate Swift data models for this app:

          Screens: {{extract_components.screens | describe}}
          Architecture: {{input.architecture}}

          Create:
          - Model structs
          - Codable conformance
          - Sample data
        response_format: "code"

    - id: generate_views
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Generate SwiftUI views:

          Design: {{item.design_spec}}
          Models: {{generate_models.data}}

          Requirements:
          - iOS 17+ APIs
          - Accessibility support
          - Dark mode support
        response_format: "code"
      loop: "{{extract_components.screens}}"

    - id: generate_viewmodels
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Generate ViewModels for {{input.architecture}}:

          Views: {{generate_views.results}}
          Models: {{generate_models.data}}

          Include:
          - State management
          - Business logic
          - API integration stubs
        response_format: "code"

    - id: create_repo
      type: integration
      connector: github
      action: create_repository
      params:
        name: "{{input.app_slug}}"
        private: true
        template: "{{config.ios_template_repo}}"

    - id: commit_code
      type: integration
      connector: github
      action: create_commit
      params:
        repo: "{{create_repo.name}}"
        files:
          - path: "Sources/Models/"
            content: "{{generate_models.data}}"
          - path: "Sources/Views/"
            content: "{{generate_views.results}}"
          - path: "Sources/ViewModels/"
            content: "{{generate_viewmodels.data}}"
        message: "feat: Initial code generation from design"

    # GATE: Code review
    - id: code_review
      type: gate
      gate_id: code-review
      criteria:
        - "Code compiles without errors"
        - "Follows Swift style guidelines"
        - "Architecture is consistent"
        - "No security vulnerabilities"
```

### Molecule 4: Build & Test Pipeline

```yaml
molecule:
  id: build-test
  name: "Build & Test Pipeline"
  description: "Build app and run tests"

  input:
    repo: string
    branch: string

  steps:
    - id: trigger_build
      type: integration
      connector: xcode_cloud
      action: start_build
      params:
        repo: "{{input.repo}}"
        branch: "{{input.branch}}"
        scheme: "{{config.scheme}}"

    - id: wait_for_build
      type: poll
      connector: xcode_cloud
      action: get_build_status
      params:
        build_id: "{{trigger_build.build_id}}"
      until: "status in ['completed', 'failed']"
      interval: 60
      timeout: 1800

    - id: run_tests
      type: integration
      connector: xcode_cloud
      action: run_tests
      params:
        build_id: "{{trigger_build.build_id}}"
        test_plan: "{{config.test_plan}}"
      condition: "wait_for_build.status == 'completed'"

    - id: browserstack_test
      type: integration
      connector: browserstack
      action: run_app_test
      params:
        app_url: "{{wait_for_build.artifact_url}}"
        devices:
          - "iPhone 15 Pro"
          - "iPhone 14"
          - "iPhone SE"
        test_suite: "smoke"
      condition: "run_tests.passed"

    - id: upload_to_testflight
      type: integration
      connector: app_store_connect
      action: upload_build
      params:
        ipa_url: "{{wait_for_build.artifact_url}}"
        whats_new: "{{input.release_notes}}"
      condition: "browserstack_test.passed"

    # GATE: QA approval
    - id: qa_approval
      type: gate
      gate_id: qa-review
      criteria:
        - "All tests pass"
        - "No critical bugs"
        - "Performance acceptable"
        - "TestFlight feedback positive"
```

### Molecule 5: App Store Submission

```yaml
molecule:
  id: app-store-submit
  name: "App Store Submission"
  description: "Submit app to App Store"

  input:
    build_id: string
    version: string

  steps:
    - id: generate_metadata
      type: integration
      connector: openai
      action: generate_text
      params:
        prompt: |
          Generate App Store metadata:

          App: {{config.app_name}}
          Description: {{config.app_description}}
          Version: {{input.version}}

          Create:
          - App Store description (4000 chars max)
          - Keywords (100 chars max)
          - What's New text
          - Promotional text
          - Support URL content

    - id: generate_screenshots
      type: integration
      connector: openai
      action: generate_image
      params:
        prompt: "App Store screenshot with device frame and marketing text"
      loop: "{{config.screenshot_specs}}"

    - id: update_metadata
      type: integration
      connector: app_store_connect
      action: update_app_info
      params:
        app_id: "{{config.app_store_id}}"
        version: "{{input.version}}"
        description: "{{generate_metadata.description}}"
        keywords: "{{generate_metadata.keywords}}"
        whats_new: "{{generate_metadata.whats_new}}"
        screenshots: "{{generate_screenshots.results}}"

    - id: submit_for_review
      type: integration
      connector: app_store_connect
      action: submit_for_review
      params:
        app_id: "{{config.app_store_id}}"
        version: "{{input.version}}"

    # GATE: Final approval before submit
    - id: submission_approval
      type: gate
      gate_id: submission-review
      criteria:
        - "All metadata complete"
        - "Screenshots meet guidelines"
        - "Privacy policy updated"
        - "Legal review complete"

    - id: notify_submitted
      type: integration
      connector: telegram
      action: send_message
      params:
        text: |
          📱 App submitted to App Store Review!

          App: {{config.app_name}}
          Version: {{input.version}}
          Build: {{input.build_id}}

          Estimated review time: 24-48 hours
```

---

## Quality Gates

### Gate 1: Concept Review
```yaml
gate:
  id: concept-review
  criteria:
    - id: feasibility
      name: "Technically feasible"
      required: true
    - id: market_fit
      name: "Market opportunity exists"
      required: true
    - id: scope
      name: "Scope appropriate for timeline"
      required: true
```

### Gate 2: Design Review
```yaml
gate:
  id: design-review
  criteria:
    - id: brand_alignment
      name: "Matches brand guidelines"
      required: true
    - id: completeness
      name: "All screens designed"
      required: true
    - id: accessibility
      name: "Accessibility considered"
      required: true
    - id: app_store_ready
      name: "Assets meet App Store requirements"
      required: true
```

### Gate 3: Code Review
```yaml
gate:
  id: code-review
  criteria:
    - id: compiles
      name: "Code compiles without errors"
      required: true
      automated: true
    - id: style
      name: "Follows Swift style guidelines"
      required: true
      automated: true
    - id: architecture
      name: "Architecture is consistent"
      required: true
    - id: security
      name: "No security vulnerabilities"
      required: true
```

### Gate 4: QA Review
```yaml
gate:
  id: qa-review
  criteria:
    - id: tests_pass
      name: "All automated tests pass"
      required: true
      automated: true
    - id: no_critical_bugs
      name: "No critical bugs"
      required: true
    - id: performance
      name: "Performance acceptable"
      required: true
    - id: testflight
      name: "TestFlight feedback addressed"
      required: false
```

### Gate 5: Submission Review
```yaml
gate:
  id: submission-review
  criteria:
    - id: metadata
      name: "All metadata complete"
      required: true
    - id: screenshots
      name: "Screenshots meet guidelines"
      required: true
    - id: privacy
      name: "Privacy policy updated"
      required: true
    - id: legal
      name: "Legal review complete"
      required: true
```

---

## Configuration

### preset.yaml
```yaml
preset:
  id: ios-app-factory
  name: "iOS App Factory"
  version: "1.0.0"
  description: "AI-powered iOS app development pipeline"

  complexity: 5

  team_size:
    min: 8
    max: 40
    default: 15

  required_integrations:
    - openai
    - github
    - cloudinary

  recommended_integrations:
    - figma
    - xcode_cloud
    - app_store_connect
    - testflight
    - firebase

  optional_integrations:
    - anthropic
    - midjourney
    - browserstack
    - revenucat
    - supabase
    - linear
    - notion

  departments:
    - product
    - design
    - development
    - qa
    - release

  molecule_templates:
    - app-concept
    - ui-design
    - swift-codegen
    - build-test
    - app-store-submit

  customization:
    required:
      - identity.name
      - identity.apple_team_id
      - github.organization
    optional:
      - design.figma_team
      - development.architecture  # MVVM, TCA, etc.
      - testing.device_matrix
      - app_store.categories
```

---

# Part 3: Integration Architecture

## Connector Attachment Model

### Simple YAML Step Syntax
```yaml
steps:
  - id: generate
    type: integration
    connector: openai      # Connector ID
    action: generate_text  # Action from connector
    params:                # Action parameters
      prompt: "..."
      model: "gpt-4o"
```

### Variable Interpolation
```yaml
params:
  prompt: "{{previous_step.output}}"
  model: "{{config.default_model}}"
```

### Conditional Execution
```yaml
condition: "previous_step.success and config.feature_enabled"
```

### Parallel Execution
```yaml
parallel: true  # Run this step in parallel with siblings
```

### Loops
```yaml
loop: "{{items_array}}"
step:
  type: integration
  connector: openai
  params:
    input: "{{item}}"
```

---

## CLI Commands

### Connect integrations
```bash
# Interactive connection
ai-corp connect openai

# With credentials
ai-corp connect openai --api-key="sk-..."

# List connected
ai-corp integrations list --connected

# Test connection
ai-corp integrations test youtube
```

### Initialize preset
```bash
# Content Factory
ai-corp init --preset=content-factory --name="My Content Studio"

# iOS App Factory
ai-corp init --preset=ios-app-factory --name="App Forge"
```

### Run workflows
```bash
# Trigger viral clone
ai-corp workflow run viral-clone --url="https://tiktok.com/..."

# Run full content pipeline
ai-corp workflow run content-pipeline --topic="AI trends 2026"
```

---

# Part 4: Implementation Roadmap

## Phase 1: Foundation (Week 1-2)
- [x] BaseConnector, CredentialVault, ConnectorRegistry
- [x] P1 Connectors: OpenAI, Anthropic, YouTube, Cloudinary, Telegram
- [ ] Molecule step types: integration, transform, gate, loop, poll
- [ ] Variable interpolation engine
- [ ] CLI integration commands

## Phase 2: Content Factory (Week 3-4)
- [ ] Content Factory preset structure
- [ ] viral-clone molecule
- [ ] avatar-video molecule
- [ ] multi-platform-publish molecule
- [ ] Content-specific gates

## Phase 3: iOS App Factory (Week 5-6)
- [ ] iOS App Factory preset structure
- [ ] app-concept molecule
- [ ] ui-design molecule
- [ ] swift-codegen molecule
- [ ] build-test molecule
- [ ] app-store-submit molecule
- [ ] P2 Connectors: Figma, GitHub, App Store Connect

## Phase 4: Additional Connectors (Week 7-8)
- [ ] HeyGen, ElevenLabs, Runway
- [ ] Instagram, TikTok, Twitter
- [ ] Xcode Cloud, TestFlight, BrowserStack
- [ ] Linear, Notion, Airtable

## Phase 5: Web UI Integration (Future)
- [ ] Visual workflow editor
- [ ] Drag-and-drop connector nodes
- [ ] Real-time execution monitoring
- [ ] Template marketplace

---

## Open Questions

1. **Credential sharing** - Should connectors be shared across presets or per-corp?
2. **Rate limiting** - How to handle API rate limits across parallel steps?
3. **Cost tracking** - Track API costs per workflow execution?
4. **Template marketplace** - Allow users to share/sell workflow templates?

---

## Related Documents

- [INTEGRATIONS_DESIGN.md](./INTEGRATIONS_DESIGN.md) - Core integrations architecture
- [AI_CORP_ARCHITECTURE.md](./AI_CORP_ARCHITECTURE.md) - Overall system architecture
- [templates/presets/](./templates/presets/) - Preset implementations
