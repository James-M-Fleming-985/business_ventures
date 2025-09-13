-- AlterTable
ALTER TABLE "cards" ADD COLUMN     "archetype" TEXT,
ADD COLUMN     "attackSpeed" DOUBLE PRECISION,
ADD COLUMN     "balanceChanges" JSONB,
ADD COLUMN     "count" INTEGER,
ADD COLUMN     "counters" JSONB,
ADD COLUMN     "damage" INTEGER,
ADD COLUMN     "deployTime" DOUBLE PRECISION,
ADD COLUMN     "description" TEXT,
ADD COLUMN     "dps" DOUBLE PRECISION,
ADD COLUMN     "gameVersion" TEXT NOT NULL DEFAULT 'current',
ADD COLUMN     "hitpoints" INTEGER,
ADD COLUMN     "imageUrl" TEXT,
ADD COLUMN     "lastBalanceDate" TIMESTAMP(3),
ADD COLUMN     "lifetime" DOUBLE PRECISION,
ADD COLUMN     "productionSpeed" DOUBLE PRECISION,
ADD COLUMN     "range" DOUBLE PRECISION,
ADD COLUMN     "spawnedUnit" TEXT,
ADD COLUMN     "speed" TEXT,
ADD COLUMN     "spellDuration" DOUBLE PRECISION,
ADD COLUMN     "spellRadius" DOUBLE PRECISION,
ADD COLUMN     "splashDamage" INTEGER,
ADD COLUMN     "splashRadius" DOUBLE PRECISION,
ADD COLUMN     "synergies" JSONB,
ADD COLUMN     "targetType" TEXT,
ADD COLUMN     "tileCoverage" JSONB,
ADD COLUMN     "usageByArena" JSONB;

-- CreateTable
CREATE TABLE "card_stats" (
    "id" TEXT NOT NULL,
    "cardId" TEXT NOT NULL,
    "gameVersion" TEXT NOT NULL,
    "hitpoints" INTEGER,
    "damage" INTEGER,
    "dps" DOUBLE PRECISION,
    "attackSpeed" DOUBLE PRECISION,
    "range" DOUBLE PRECISION,
    "splashRadius" DOUBLE PRECISION,
    "splashDamage" INTEGER,
    "deployTime" DOUBLE PRECISION,
    "lifetime" DOUBLE PRECISION,
    "spellDuration" DOUBLE PRECISION,
    "cost" INTEGER,
    "changeDescription" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "releaseDate" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "card_stats_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "card_stats_gameVersion_idx" ON "card_stats"("gameVersion");

-- CreateIndex
CREATE INDEX "card_stats_isActive_idx" ON "card_stats"("isActive");

-- CreateIndex
CREATE UNIQUE INDEX "card_stats_cardId_gameVersion_key" ON "card_stats"("cardId", "gameVersion");

-- CreateIndex
CREATE INDEX "cards_gameVersion_idx" ON "cards"("gameVersion");

-- CreateIndex
CREATE INDEX "cards_category_idx" ON "cards"("category");

-- CreateIndex
CREATE INDEX "cards_cost_idx" ON "cards"("cost");

-- AddForeignKey
ALTER TABLE "placement_analyses" ADD CONSTRAINT "placement_analyses_placedCard_fkey" FOREIGN KEY ("placedCard") REFERENCES "cards"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "card_stats" ADD CONSTRAINT "card_stats_cardId_fkey" FOREIGN KEY ("cardId") REFERENCES "cards"("id") ON DELETE CASCADE ON UPDATE CASCADE;
