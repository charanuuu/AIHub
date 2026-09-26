from typing import List, Optional
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    title: str = Field(..., description="Article headline")
    source: str = Field(..., description="Publisher or news source name")
    url: Optional[str] = Field(None, description="Direct URL link to article")
    published_at: Optional[str] = Field(None, description="Publication timestamp or date string")
    summary: Optional[str] = Field(None, description="Brief snippet or summary of the article")


class NewsInput(BaseModel):
    query: Optional[str] = Field(None, description="Topic, company, or search query (e.g. 'artificial intelligence', 'NASA', 'Apple')")
    category: Optional[str] = Field("general", description="News category: 'general', 'technology', 'business', 'science', 'health', 'entertainment', 'sports'")
    limit: Optional[int] = Field(5, ge=1, le=10, description="Maximum number of articles to return (1 to 10)")


class NewsOutput(BaseModel):
    topic: str = Field(..., description="Search topic or category queried")
    category: str = Field(..., description="News category")
    total_results: int = Field(..., description="Number of articles returned")
    articles: List[NewsArticle] = Field(default_factory=list, description="List of articles")
    provider: str = Field(..., description="News data provider name")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
