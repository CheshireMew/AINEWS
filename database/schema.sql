-- 加密新闻聚合系统数据库结构

-- 新闻主表
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    
    -- 基础信息
    title VARCHAR(1000) NOT NULL,
    content TEXT,
    source_url VARCHAR(2000) UNIQUE NOT NULL,
    source_site VARCHAR(50) NOT NULL,
    
    -- 时间戳
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    -- 网站原生重要标记
    is_marked_important BOOLEAN DEFAULT FALSE,
    site_importance_flag VARCHAR(100),
    
    -- 处理阶段: raw/keyword_filtered/ai_processed/pushed
    processing_stage VARCHAR(20) DEFAULT 'raw',
    
    -- 关键词过滤结果
    keyword_filter_passed BOOLEAN,
    keyword_filter_reason VARCHAR(200),
    keyword_matched_whitelist BOOLEAN DEFAULT FALSE,
    filtered_at TIMESTAMP,
    
    -- AI处理结果
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_score FLOAT,
    ai_summary VARCHAR(500),
    ai_processed_at TIMESTAMP,
    
    -- 去重信息
    duplicate_of INT REFERENCES news(id) ON DELETE SET NULL,
    is_duplicate BOOLEAN DEFAULT FALSE,
    similarity_score FLOAT,
    multiple_sources TEXT[], -- 多个来源合并
    
    -- 推送状态
    pushed BOOLEAN DEFAULT FALSE,
    pushed_at TIMESTAMP,
    push_batch_id UUID,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    description TEXT,
    enabled_for_push BOOLEAN DEFAULT TRUE,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 新闻-标签关联表
CREATE TABLE IF NOT EXISTS news_tags (
    news_id INT REFERENCES news(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    confidence FLOAT,
    PRIMARY KEY (news_id, tag_id)
);

-- 处理日志表
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    news_id INT REFERENCES news(id) ON DELETE CASCADE,
    stage VARCHAR(20) NOT NULL,
    action VARCHAR(50) NOT NULL,
    reason TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 推送记录表
CREATE TABLE IF NOT EXISTS push_logs (
    id SERIAL PRIMARY KEY,
    batch_id UUID UNIQUE NOT NULL,
    news_count INT,
    tag_filters VARCHAR(200),
    channel VARCHAR(50),
    pushed_at TIMESTAMP DEFAULT NOW()
);

-- 过滤规则统计表
CREATE TABLE IF NOT EXISTS filter_stats (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(20),
    rule_pattern VARCHAR(500),
    rule_reason VARCHAR(200),
    hit_count INT DEFAULT 0,
    last_hit_at TIMESTAMP,
    date DATE DEFAULT CURRENT_DATE,
    UNIQUE(rule_pattern, date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_news_source_url ON news(source_url);
CREATE INDEX IF NOT EXISTS idx_news_processing_stage ON news(processing_stage);
CREATE INDEX IF NOT EXISTS idx_news_scraped_at ON news(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_ai_score ON news(ai_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_duplicate ON news(is_duplicate, duplicate_of);
CREATE INDEX IF NOT EXISTS idx_processing_logs_news_id ON processing_logs(news_id);
CREATE INDEX IF NOT EXISTS idx_filter_stats_date ON filter_stats(date DESC);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_news_updated_at BEFORE UPDATE ON news
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
