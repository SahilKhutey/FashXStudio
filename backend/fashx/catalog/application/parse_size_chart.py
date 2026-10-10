from dataclasses import dataclass
from typing import Any
from uuid import UUID

from database.models.catalog import SizeChart, SizeMeasurement
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.sizing.size_parser import SizeChartParser
from fashx.core.errors import EntityNotFoundError


@dataclass
class ParseSizeChartCommand:
    garment_id: UUID
    storage_key: str
    raw_rows: list[dict[str, Any]]
    default_unit: str = "cm"


@dataclass
class ParseSizeChartResult:
    size_chart_id: UUID
    garment_id: UUID
    review_status: str
    measurements: list[dict[str, Any]]


class ParseSizeChartUseCase:
    """Use case to parse raw retailer size tables into normalized centimeter size measurements."""

    def __init__(self, uow: CatalogUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: ParseSizeChartCommand) -> ParseSizeChartResult:
        async with self.uow:
            garment = await self.uow.canonical_garments.get_by_id(cmd.garment_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", cmd.garment_id)

            parsed_rows = SizeChartParser.parse_table(cmd.raw_rows, cmd.default_unit)
            has_review_flag = any(r.needs_review for r in parsed_rows)
            review_status = "review_required" if has_review_flag else "completed"

            chart = SizeChart(
                garment_id=garment.id,
                storage_key=cmd.storage_key,
                parser_version="size-parser-v1",
                review_status=review_status,
                raw_ocr_json={"rows": cmd.raw_rows},
            )
            self.uow.size_charts.add(chart)
            await self.uow.flush()

            saved_measurements: list[dict[str, Any]] = []
            for row in parsed_rows:
                meas = SizeMeasurement(
                    size_chart_id=chart.id,
                    garment_id=garment.id,
                    size_label=row.size_label,
                    chest_cm=row.chest_cm,
                    length_cm=row.length_cm,
                    waist_cm=row.waist_cm,
                    shoulder_cm=row.shoulder_cm,
                    source="size_chart",
                    confidence=row.confidence,
                    needs_review=row.needs_review,
                )
                self.uow.size_measurements.add(meas)
                saved_measurements.append(
                    {
                        "size_label": row.size_label,
                        "chest_cm": row.chest_cm,
                        "length_cm": row.length_cm,
                        "waist_cm": row.waist_cm,
                        "shoulder_cm": row.shoulder_cm,
                        "confidence": row.confidence,
                        "needs_review": row.needs_review,
                    }
                )

            await self.uow.flush()
            await self.uow.commit()

            return ParseSizeChartResult(
                size_chart_id=chart.id,
                garment_id=garment.id,
                review_status=review_status,
                measurements=saved_measurements,
            )
