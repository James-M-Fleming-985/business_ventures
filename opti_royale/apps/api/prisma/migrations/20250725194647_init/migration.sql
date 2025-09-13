-- CreateEnum
CREATE TYPE "SkillLevel" AS ENUM ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', 'PROFESSIONAL');

-- CreateEnum
CREATE TYPE "VideoStatus" AS ENUM ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED');

-- CreateEnum
CREATE TYPE "MatchResult" AS ENUM ('WIN', 'LOSS', 'DRAW');

-- CreateEnum
CREATE TYPE "AchievementCategory" AS ENUM ('PLACEMENT_MASTERY', 'IMPROVEMENT', 'CONSISTENCY', 'SOCIAL', 'MILESTONE');

-- CreateEnum
CREATE TYPE "AchievementRarity" AS ENUM ('COMMON', 'RARE', 'EPIC', 'LEGENDARY', 'CHAMPION');

-- CreateEnum
CREATE TYPE "SubscriptionPlan" AS ENUM ('FREE', 'PREMIUM', 'PRO');

-- CreateEnum
CREATE TYPE "SubscriptionStatus" AS ENUM ('ACTIVE', 'CANCELED', 'PAST_DUE', 'INCOMPLETE', 'TRIALING');

-- CreateEnum
CREATE TYPE "EventType" AS ENUM ('USER_ACTION', 'PLACEMENT_ANALYSIS', 'VIDEO_UPLOAD', 'SUBSCRIPTION', 'ACHIEVEMENT', 'ERROR', 'PERFORMANCE');

-- CreateEnum
CREATE TYPE "CardType" AS ENUM ('TROOP', 'SPELL', 'BUILDING');

-- CreateEnum
CREATE TYPE "CardRarity" AS ENUM ('COMMON', 'RARE', 'EPIC', 'LEGENDARY', 'CHAMPION');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "avatar" TEXT,
    "clashRoyaleTag" TEXT,
    "trophyCount" INTEGER DEFAULT 0,
    "kingLevel" INTEGER DEFAULT 1,
    "favoriteArchetype" TEXT,
    "skillLevel" "SkillLevel" NOT NULL DEFAULT 'BEGINNER',
    "isEmailVerified" BOOLEAN NOT NULL DEFAULT false,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "premiumExpiresAt" TIMESTAMP(3),
    "lastActiveAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "videos" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "filename" TEXT NOT NULL,
    "originalName" TEXT NOT NULL,
    "fileSize" INTEGER NOT NULL,
    "duration" DOUBLE PRECISION,
    "resolution" TEXT,
    "fps" INTEGER,
    "status" "VideoStatus" NOT NULL DEFAULT 'UPLOADED',
    "processingStartedAt" TIMESTAMP(3),
    "processingCompletedAt" TIMESTAMP(3),
    "errorMessage" TEXT,
    "gameMode" TEXT,
    "matchResult" "MatchResult",
    "playerDeck" JSONB,
    "opponentDeck" JSONB,
    "azureBlobUrl" TEXT NOT NULL,
    "thumbnailUrl" TEXT,
    "processedVideoUrl" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "videos_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "placement_analyses" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "videoId" TEXT NOT NULL,
    "frameTimestamp" DOUBLE PRECISION NOT NULL,
    "gameTimestamp" DOUBLE PRECISION,
    "elixirCount" INTEGER,
    "opponentElixir" INTEGER,
    "placedCard" TEXT NOT NULL,
    "userPlacement" JSONB NOT NULL,
    "optimalPlacement" JSONB NOT NULL,
    "placementScore" DOUBLE PRECISION NOT NULL,
    "confidenceLevel" DOUBLE PRECISION NOT NULL,
    "feedbackMessage" TEXT NOT NULL,
    "strategicReasoning" TEXT NOT NULL,
    "improvementTip" TEXT,
    "boardState" JSONB NOT NULL,
    "tacticalSituation" TEXT,
    "userRating" INTEGER,
    "wasHelpful" BOOLEAN,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "placement_analyses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "progress_tracking" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "trackingDate" TIMESTAMP(3) NOT NULL,
    "weekNumber" INTEGER NOT NULL,
    "monthNumber" INTEGER NOT NULL,
    "totalAnalyses" INTEGER NOT NULL DEFAULT 0,
    "averagePlacementScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "bestPlacementScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "worstPlacementScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "mostAnalyzedCard" TEXT,
    "strongestCard" TEXT,
    "weakestCard" TEXT,
    "scoreImprovement" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "consistencyScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "learningVelocity" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "sessionsCount" INTEGER NOT NULL DEFAULT 0,
    "avgSessionDuration" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "videosUploaded" INTEGER NOT NULL DEFAULT 0,
    "skillLevelProgress" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "masteredConcepts" JSONB NOT NULL DEFAULT '[]',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "progress_tracking_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "achievements" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "category" "AchievementCategory" NOT NULL,
    "rarity" "AchievementRarity" NOT NULL,
    "unlockCriteria" JSONB NOT NULL,
    "xpReward" INTEGER NOT NULL DEFAULT 0,
    "iconUrl" TEXT,
    "badgeColor" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "achievements_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_achievements" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "achievementId" TEXT NOT NULL,
    "unlockedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "progress" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "triggerData" JSONB,

    CONSTRAINT "user_achievements_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "subscriptions" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "planType" "SubscriptionPlan" NOT NULL,
    "status" "SubscriptionStatus" NOT NULL,
    "currentPeriodStart" TIMESTAMP(3) NOT NULL,
    "currentPeriodEnd" TIMESTAMP(3) NOT NULL,
    "cancelAtPeriodEnd" BOOLEAN NOT NULL DEFAULT false,
    "stripeCustomerId" TEXT,
    "stripeSubscriptionId" TEXT,
    "stripePriceId" TEXT,
    "analysesUsedThisPeriod" INTEGER NOT NULL DEFAULT 0,
    "analysesLimit" INTEGER NOT NULL DEFAULT 5,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "subscriptions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "analytics_events" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "eventType" "EventType" NOT NULL,
    "eventName" TEXT NOT NULL,
    "properties" JSONB NOT NULL,
    "sessionId" TEXT,
    "deviceInfo" JSONB,
    "userAgent" TEXT,
    "ipAddress" TEXT,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "analytics_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "cards" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "type" "CardType" NOT NULL,
    "rarity" "CardRarity" NOT NULL,
    "cost" INTEGER NOT NULL,
    "category" TEXT NOT NULL,
    "tags" JSONB NOT NULL,
    "pickRate" DOUBLE PRECISION,
    "winRate" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "cards_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_username_key" ON "users"("username");

-- CreateIndex
CREATE UNIQUE INDEX "users_clashRoyaleTag_key" ON "users"("clashRoyaleTag");

-- CreateIndex
CREATE INDEX "users_email_idx" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_clashRoyaleTag_idx" ON "users"("clashRoyaleTag");

-- CreateIndex
CREATE INDEX "users_lastActiveAt_idx" ON "users"("lastActiveAt");

-- CreateIndex
CREATE INDEX "videos_status_idx" ON "videos"("status");

-- CreateIndex
CREATE INDEX "videos_userId_createdAt_idx" ON "videos"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "placement_analyses_userId_createdAt_idx" ON "placement_analyses"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "placement_analyses_videoId_idx" ON "placement_analyses"("videoId");

-- CreateIndex
CREATE INDEX "placement_analyses_placedCard_idx" ON "placement_analyses"("placedCard");

-- CreateIndex
CREATE INDEX "placement_analyses_placementScore_idx" ON "placement_analyses"("placementScore");

-- CreateIndex
CREATE INDEX "progress_tracking_userId_trackingDate_idx" ON "progress_tracking"("userId", "trackingDate");

-- CreateIndex
CREATE INDEX "progress_tracking_weekNumber_idx" ON "progress_tracking"("weekNumber");

-- CreateIndex
CREATE INDEX "progress_tracking_monthNumber_idx" ON "progress_tracking"("monthNumber");

-- CreateIndex
CREATE UNIQUE INDEX "progress_tracking_userId_trackingDate_key" ON "progress_tracking"("userId", "trackingDate");

-- CreateIndex
CREATE UNIQUE INDEX "user_achievements_userId_achievementId_key" ON "user_achievements"("userId", "achievementId");

-- CreateIndex
CREATE UNIQUE INDEX "subscriptions_stripeSubscriptionId_key" ON "subscriptions"("stripeSubscriptionId");

-- CreateIndex
CREATE INDEX "subscriptions_userId_idx" ON "subscriptions"("userId");

-- CreateIndex
CREATE INDEX "subscriptions_status_idx" ON "subscriptions"("status");

-- CreateIndex
CREATE INDEX "subscriptions_stripeSubscriptionId_idx" ON "subscriptions"("stripeSubscriptionId");

-- CreateIndex
CREATE INDEX "analytics_events_eventType_timestamp_idx" ON "analytics_events"("eventType", "timestamp");

-- CreateIndex
CREATE INDEX "analytics_events_userId_timestamp_idx" ON "analytics_events"("userId", "timestamp");

-- CreateIndex
CREATE INDEX "analytics_events_sessionId_idx" ON "analytics_events"("sessionId");

-- AddForeignKey
ALTER TABLE "videos" ADD CONSTRAINT "videos_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "placement_analyses" ADD CONSTRAINT "placement_analyses_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "placement_analyses" ADD CONSTRAINT "placement_analyses_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "videos"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "progress_tracking" ADD CONSTRAINT "progress_tracking_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_achievements" ADD CONSTRAINT "user_achievements_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_achievements" ADD CONSTRAINT "user_achievements_achievementId_fkey" FOREIGN KEY ("achievementId") REFERENCES "achievements"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "subscriptions" ADD CONSTRAINT "subscriptions_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "analytics_events" ADD CONSTRAINT "analytics_events_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
