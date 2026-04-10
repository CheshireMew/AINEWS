import React from 'react';
import PropTypes from 'prop-types';
import { Button, Input, Card, Row, Col } from 'antd';

export default function DuplicateSimilarityCard({
    contentKind,
    newsId1,
    newsId2,
    similarityResult,
    checkingLoading,
    setNewsId1,
    setNewsId2,
    checkSimilarity,
}) {
    return (
        <Card title={contentKind === 'article' ? '🔍 文章相似度检测工具' : '🔍 快讯相似度检测工具'} size="small" style={{ marginBottom: '16px' }}>
            <Row gutter={[8, 8]} align="middle">
                <Col><Input placeholder={contentKind === 'article' ? '文章ID 1' : '快讯ID 1'} value={newsId1} onChange={(event) => setNewsId1(event.target.value)} style={{ width: '120px' }} /></Col>
                <Col><Input placeholder={contentKind === 'article' ? '文章ID 2' : '快讯ID 2'} value={newsId2} onChange={(event) => setNewsId2(event.target.value)} style={{ width: '120px' }} /></Col>
                <Col><Button type="primary" onClick={checkSimilarity} loading={checkingLoading}>检测相似度</Button></Col>
                {similarityResult && (
                    <Col flex="auto">
                        <div style={{ background: similarityResult.is_duplicate ? '#f6ffed' : '#fff7e6', padding: '8px 12px', borderRadius: '4px' }}>
                            相似度: {(similarityResult.similarity * 100).toFixed(2)}% | {similarityResult.is_duplicate ? '✅ 判定为重复' : '❌ 未达阈值'}
                        </div>
                    </Col>
                )}
            </Row>
        </Card>
    );
}

DuplicateSimilarityCard.propTypes = {
    contentKind: PropTypes.string.isRequired,
    newsId1: PropTypes.string.isRequired,
    newsId2: PropTypes.string.isRequired,
    similarityResult: PropTypes.shape({
        similarity: PropTypes.number.isRequired,
        is_duplicate: PropTypes.bool.isRequired,
    }),
    checkingLoading: PropTypes.bool.isRequired,
    setNewsId1: PropTypes.func.isRequired,
    setNewsId2: PropTypes.func.isRequired,
    checkSimilarity: PropTypes.func.isRequired,
};
