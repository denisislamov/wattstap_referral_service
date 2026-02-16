"""
Mining Balance Service.

Handles CRUD for mining balance configuration and seeding from CSV data.
"""

import csv
import io
import os
import re
from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.mining_balance import MiningBalanceParams, MiningBalanceDailyProgression
from app.schemas.mining_balance import (
    MiningBalanceResponse,
    DailyProgressionItem,
    MiningBalanceUpdateRequest,
    DailyProgressionCreate,
)


class MiningBalanceService:
    """Service for managing mining balance configuration."""

    # ──────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────

    async def get_active_balance(
        self, db: AsyncSession, version: str = "default"
    ) -> Optional[MiningBalanceParams]:
        """Get the active balance params with daily progression eagerly loaded."""
        result = await db.execute(
            select(MiningBalanceParams)
            .options(selectinload(MiningBalanceParams.daily_progression))
            .where(
                MiningBalanceParams.version == version,
                MiningBalanceParams.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    def params_to_response(self, params: MiningBalanceParams) -> MiningBalanceResponse:
        """Convert DB model to API response schema."""
        daily = sorted(params.daily_progression, key=lambda d: d.day)

        return MiningBalanceResponse(
            coinsPerTap=params.coins_per_tap,
            expPerTap=params.exp_per_tap,
            energyCostPerTap=params.energy_cost_per_tap,
            startCapacityHits=params.start_capacity_hits,
            cooldownPerHitSec=params.cooldown_per_hit_sec,
            critMultiplier=params.crit_multiplier,
            chanceCritPercent=params.chance_crit_percent,
            avgPlaytimeMinutes=params.avg_playtime_minutes,
            tapsPerSecond=params.taps_per_second,
            profitPerHour=params.profit_per_hour,
            maxHoursOffline=params.max_hours_offline,
            sessionsPerDay=params.sessions_per_day,
            dailyProgression=[
                DailyProgressionItem(
                    day=d.day,
                    playtimeSec=d.playtime_sec,
                    tapsPerSession=d.taps_per_session,
                    tapsPerDay=d.taps_per_day,
                    expPerDay=d.exp_per_day,
                    coinsFromTaps=d.coins_from_taps,
                    coinsFromOfflineBonus=d.coins_from_offline_bonus,
                    profitCoins=d.profit_coins,
                    cumulativeProfitCoins=d.cumulative_profit_coins,
                    cumulativeExp=d.cumulative_exp,
                )
                for d in daily
            ],
        )

    # ──────────────────────────────────────────
    # Update (admin)
    # ──────────────────────────────────────────

    async def update_balance(
        self,
        db: AsyncSession,
        update: MiningBalanceUpdateRequest,
        version: str = "default",
    ) -> Tuple[bool, Optional[MiningBalanceParams], str]:
        """Update balance params and/or daily progression."""
        params = await self.get_active_balance(db, version)
        if not params:
            return False, None, f"Balance version '{version}' not found"

        # Update scalar fields
        field_map = {
            "coinsPerTap": "coins_per_tap",
            "expPerTap": "exp_per_tap",
            "energyCostPerTap": "energy_cost_per_tap",
            "startCapacityHits": "start_capacity_hits",
            "cooldownPerHitSec": "cooldown_per_hit_sec",
            "critMultiplier": "crit_multiplier",
            "chanceCritPercent": "chance_crit_percent",
            "avgPlaytimeMinutes": "avg_playtime_minutes",
            "tapsPerSecond": "taps_per_second",
            "profitPerHour": "profit_per_hour",
            "maxHoursOffline": "max_hours_offline",
            "sessionsPerDay": "sessions_per_day",
        }

        for schema_field, model_field in field_map.items():
            value = getattr(update, schema_field, None)
            if value is not None:
                setattr(params, model_field, value)

        # Update daily progression if provided
        if update.dailyProgression is not None:
            await self._replace_daily_progression(db, params, update.dailyProgression)

        params.updated_at = datetime.utcnow()
        await db.flush()
        
        # Re-load to get fresh daily progression
        refreshed = await self.get_active_balance(db, version)
        return True, refreshed, "Balance updated successfully"

    async def _replace_daily_progression(
        self,
        db: AsyncSession,
        params: MiningBalanceParams,
        items: List[DailyProgressionCreate],
    ):
        """Replace all daily progression rows for a given params record."""
        # Delete existing
        for existing in list(params.daily_progression):
            await db.delete(existing)
        await db.flush()

        # Insert new
        for item in items:
            row = MiningBalanceDailyProgression(
                balance_params_id=params.id,
                day=item.day,
                playtime_sec=item.playtimeSec,
                taps_per_session=item.tapsPerSession,
                taps_per_day=item.tapsPerDay,
                exp_per_day=item.expPerDay,
                coins_from_taps=item.coinsFromTaps,
                coins_from_offline_bonus=item.coinsFromOfflineBonus,
                profit_coins=item.profitCoins,
                cumulative_profit_coins=item.cumulativeProfitCoins,
                cumulative_exp=item.cumulativeExp,
            )
            db.add(row)

    # ──────────────────────────────────────────
    # Seed from CSV
    # ──────────────────────────────────────────

    async def seed_from_csv(
        self,
        db: AsyncSession,
        csv_text: str,
        version: str = "default",
        force: bool = False,
    ) -> Tuple[bool, str, int]:
        """
        Seed balance data from CSV text (WattsBalanceMining.csv format).
        
        Returns (success, message, days_count).
        If balance already exists and force=False, skip seeding.
        """
        existing = await self.get_active_balance(db, version)
        if existing and not force:
            days_count = len(existing.daily_progression)
            return True, f"Balance '{version}' already exists with {days_count} days — skipping seed", days_count

        # Parse CSV
        start_params, daily_data = self._parse_csv(csv_text)

        if existing and force:
            # Delete old and recreate
            await db.delete(existing)
            await db.flush()

        # Create params record
        params = MiningBalanceParams(
            version=version,
            is_active=True,
            coins_per_tap=start_params.get("coins_per_tap", 1),
            exp_per_tap=start_params.get("exp_per_tap", 1),
            energy_cost_per_tap=start_params.get("energy_cost_per_tap", 0),
            start_capacity_hits=start_params.get("start_capacity_hits", 1500),
            cooldown_per_hit_sec=start_params.get("cooldown_per_hit_sec", 2.0),
            crit_multiplier=start_params.get("crit_multiplier", 1.2),
            chance_crit_percent=start_params.get("chance_crit_percent", 1.0),
            avg_playtime_minutes=start_params.get("avg_playtime_minutes", 15),
            taps_per_second=start_params.get("taps_per_second", 10),
            profit_per_hour=start_params.get("profit_per_hour", 500),
            max_hours_offline=start_params.get("max_hours_offline", 3),
            sessions_per_day=start_params.get("sessions_per_day", 2),
        )
        db.add(params)
        await db.flush()  # get params.id

        # Create daily progression rows
        for day_data in daily_data:
            row = MiningBalanceDailyProgression(
                balance_params_id=params.id,
                **day_data,
            )
            db.add(row)

        await db.commit()

        days_count = len(daily_data)
        action = "re-seeded" if force else "seeded"
        return True, f"Balance '{version}' {action} with {days_count} days", days_count

    async def seed_from_csv_file(
        self,
        db: AsyncSession,
        csv_path: str,
        version: str = "default",
        force: bool = False,
    ) -> Tuple[bool, str, int]:
        """Seed balance from a CSV file on disk."""
        if not os.path.exists(csv_path):
            return False, f"CSV file not found: {csv_path}", 0

        with open(csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()

        return await self.seed_from_csv(db, csv_text, version, force)

    # ──────────────────────────────────────────
    # CSV parsing helpers
    # ──────────────────────────────────────────

    def _parse_csv(self, csv_text: str) -> Tuple[dict, list]:
        """
        Parse WattsBalanceMining.csv format.
        
        Returns (start_params_dict, list_of_daily_dicts).
        """
        lines = [line for line in csv_text.strip().split("\n") if line.strip()]

        start_params = {}
        daily_data = []

        # Parameter name -> dict key mapping
        param_map = {
            "Coins Per tap": "coins_per_tap",
            "Exp per Tap": "exp_per_tap",
            "Start Capacity Hits": "start_capacity_hits",
            "Coldown 1hits  sec": "cooldown_per_hit_sec",
            "Crit multiplier": "crit_multiplier",
            "Chance Crit %": "chance_crit_percent",
            "Avg Playtime (mins)": "avg_playtime_minutes",
            "Taps per second": "taps_per_second",
            "Profit per Hour": "profit_per_hour",
            "Max Hours offline": "max_hours_offline",
            "Sessions per day": "sessions_per_day",
        }
        int_fields = {
            "coins_per_tap", "exp_per_tap", "start_capacity_hits",
            "avg_playtime_minutes", "taps_per_second", "profit_per_hour",
            "max_hours_offline", "sessions_per_day",
        }
        float_fields = {
            "cooldown_per_hit_sec", "crit_multiplier", "chance_crit_percent",
        }

        # ── Parse start parameters ──
        for line in lines:
            parts = self._split_csv_line(line)
            if len(parts) < 2:
                continue
            name = parts[0].strip()
            if name in param_map:
                key = param_map[name]
                raw = parts[1].strip()
                if key in int_fields:
                    start_params[key] = self._parse_int(raw, 0)
                elif key in float_fields:
                    start_params[key] = self._parse_float(raw, 0.0)

        # ── Find daily progression header row ──
        header_idx = -1
        for i, line in enumerate(lines):
            if "Day 1" in line and "Day 2" in line:
                header_idx = i
                break

        if header_idx == -1:
            return start_params, daily_data

        # Row name -> (dict key, type)
        row_map = {
            "Playtime (sec)": ("playtime_sec", int),
            "Taps per session": ("taps_per_session", int),
            "Taps per day": ("taps_per_day", int),
            "Exp per day": ("exp_per_day", int),
            "Coins from taps": ("coins_from_taps", float),
            "Coins from offline bonus": ("coins_from_offline_bonus", float),
            "Profit Coins": ("profit_coins", float),
            "Cumulative profit coins": ("cumulative_profit_coins", float),
            "Cumulative exp": ("cumulative_exp", int),
        }

        # Build a dict: row_key -> [values for day1..day30]
        row_values = {}
        for i in range(header_idx + 1, min(header_idx + 15, len(lines))):
            parts = self._split_csv_line(lines[i])
            if len(parts) < 2:
                continue
            row_name = parts[0].strip()
            if row_name in row_map:
                row_values[row_name] = parts[1:]  # day values

        # Determine how many days
        num_days = 30
        for vals in row_values.values():
            num_days = min(num_days, len(vals))
        if num_days == 0:
            num_days = 30

        # Build daily data dicts
        for day_idx in range(num_days):
            day_dict = {"day": day_idx + 1}
            for row_name, (key, typ) in row_map.items():
                if row_name in row_values and day_idx < len(row_values[row_name]):
                    raw = row_values[row_name][day_idx].strip()
                    if typ == int:
                        day_dict[key] = self._parse_int(raw, 0)
                    else:
                        day_dict[key] = self._parse_float(raw, 0.0)
            daily_data.append(day_dict)

        return start_params, daily_data

    @staticmethod
    def _split_csv_line(line: str) -> list:
        """Split CSV line respecting quoted fields (handles comma-as-decimal like '3946,8')."""
        result = []
        current = ""
        in_quotes = False
        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == ',' and not in_quotes:
                result.append(current)
                current = ""
            else:
                current += ch
        result.append(current)
        return result

    @staticmethod
    def _parse_int(value: str, default: int = 0) -> int:
        """Parse integer, handling European decimal comma format."""
        if not value or not value.strip():
            return default
        value = value.strip().replace(" ", "").replace(",", ".")
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _parse_float(value: str, default: float = 0.0) -> float:
        """Parse float, handling European decimal comma format."""
        if not value or not value.strip():
            return default
        value = value.strip().replace(" ", "").replace(",", ".")
        try:
            return float(value)
        except (ValueError, TypeError):
            return default


# Singleton instance
mining_balance_service = MiningBalanceService()
