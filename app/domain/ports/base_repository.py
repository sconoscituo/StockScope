from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    """헥사고날 아키텍처 - 저장소 포트 (인바운드/아웃바운드 경계 정의)"""

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """ID로 단일 엔티티 조회"""
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[T]:
        """전체 엔티티 목록 조회"""
        raise NotImplementedError

    @abstractmethod
    async def create(self, entity: T) -> T:
        """엔티티 생성"""
        raise NotImplementedError

    @abstractmethod
    async def update(self, id: int, entity: T) -> Optional[T]:
        """엔티티 수정"""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """엔티티 삭제"""
        raise NotImplementedError
