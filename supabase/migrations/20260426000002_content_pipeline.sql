-- Content Briefs
CREATE TABLE IF NOT EXISTS content_briefs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  segment TEXT NOT NULL,
  theme TEXT NOT NULL,
  hook TEXT,
  emotion TEXT,
  format TEXT,
  platform TEXT,
  copy_direction TEXT,
  visual_direction TEXT,
  image_prompt TEXT,
  caption TEXT,
  hashtags TEXT[],
  cta TEXT,
  best_time TEXT,
  content_references TEXT[],
  generated_image_url TEXT,
  status TEXT DEFAULT 'brief_ready' CHECK (status IN ('brief_ready','image_generated','post_scheduled','published','archived')),
  created_by TEXT DEFAULT 'strategist',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated Creatives
CREATE TABLE IF NOT EXISTS generated_creatives (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  brief_id UUID REFERENCES content_briefs(id) ON DELETE CASCADE,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  image_url TEXT NOT NULL,
  provider TEXT DEFAULT 'freepik',
  prompt_used TEXT,
  aspect_ratio TEXT,
  style TEXT,
  caption TEXT,
  hashtags TEXT[],
  platform TEXT,
  status TEXT DEFAULT 'generated' CHECK (status IN ('generated','approved','rejected','scheduled','published')),
  scheduled_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_briefs_client ON content_briefs(client_id);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON content_briefs(status);
CREATE INDEX IF NOT EXISTS idx_creatives_brief ON generated_creatives(brief_id);
CREATE INDEX IF NOT EXISTS idx_creatives_status ON generated_creatives(status);

CREATE TRIGGER trg_briefs_updated BEFORE UPDATE ON content_briefs FOR EACH ROW EXECUTE FUNCTION update_updated_at();
