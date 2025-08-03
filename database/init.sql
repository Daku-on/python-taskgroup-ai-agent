-- Claude Code Knowledge Base初期化スクリプト

-- ナレッジベーステーブル作成
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 全文検索用のインデックス
CREATE INDEX IF NOT EXISTS idx_knowledge_content_search 
ON knowledge_base USING gin(to_tsvector('english', title || ' ' || content));

-- カテゴリ用インデックス
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category);

-- タグ用インデックス
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_base USING gin(tags);

-- 更新時刻自動更新関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 更新時刻トリガー
CREATE TRIGGER update_knowledge_base_updated_at 
    BEFORE UPDATE ON knowledge_base 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();