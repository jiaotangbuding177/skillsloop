# Scoped Prisma model projection

Derived from boundary excerpts. Not a complete Prisma schema; source line numbers below are authoritative.

## User
Source: packages/db/prisma/schema.prisma:12

      id           String   @id @default(uuid())
      role         String   @default("user")
      status       String   @default("active")
      locale       String   @default("zh")
## Enterprise
Source: packages/db/prisma/schema.prisma:98

      id                           String   @id @default(uuid())
      name                         String   @unique
      slug                         String   @unique
      status                       String   @default("active")
      inheritGlobalSkillCategories Boolean  @default(true)
      inheritGlobalAgentCategories Boolean  @default(true)
      enterpriseKind               String   @default("b2b")
      instanceAssignmentStrategy   String   @default("recent_usage_first")
      instanceAssignmentState      Json?
      logoOssKey                   String?
      avatarOssKey                 String?
      /// B 端企业是否开启「记忆模式」；成员可见「我的记忆」入口
      memoryEnabled                Boolean  @default(false)
      /// B 端是否开启 Skill 自动涌现（管理员一开即对组织生效，无成员二次授权）
      skillEmergenceEnabled        Boolean  @default(false)
      /// Skill 自动涌现评估周期（天），1–30
      skillEmergenceIntervalDays   Int      @default(1)
      /// When true, packaged drafts auto-activate as personal Skills (skip user confirm).
      skillEmergenceAutoAcceptPersonal Boolean @default(false)
      createdBy                    String?
## EnterpriseDepartment
Source: packages/db/prisma/schema.prisma:202

      id           String   @id @default(uuid())
      enterpriseId String
      name         String
      sortOrder    Int      @default(0)
      createdAt    DateTime @default(now())
      updatedAt    DateTime @updatedAt
      isDeleted    Boolean  @default(false)
      enterprise Enterprise                  @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      groups     EnterpriseDepartmentGroup[]
      @@index([enterpriseId, isDeleted, sortOrder])
      @@map("enterprise_departments")
    }
## EnterpriseDepartmentGroup
Source: packages/db/prisma/schema.prisma:218

      id           String   @id @default(uuid())
      departmentId String
      enterpriseId String
      name         String
      sortOrder    Int      @default(0)
      createdAt    DateTime @default(now())
      updatedAt    DateTime @updatedAt
      isDeleted    Boolean  @default(false)
      department EnterpriseDepartment              @relation(fields: [departmentId], references: [id], onDelete: Cascade)
      members    EnterpriseDepartmentGroupMember[]
      @@index([departmentId, isDeleted, sortOrder])
      @@index([enterpriseId, isDeleted])
      @@map("enterprise_department_groups")
    }
## EnterpriseDepartmentGroupMember
Source: packages/db/prisma/schema.prisma:236

      id           String   @id @default(uuid())
      groupId      String
      departmentId String
      userId       String
      createdAt    DateTime @default(now())
      group EnterpriseDepartmentGroup @relation(fields: [groupId], references: [id], onDelete: Cascade)
      @@unique([groupId, userId])
      @@unique([departmentId, userId])
      @@index([userId])
      @@map("enterprise_department_group_members")
    }
## EnterpriseMembership
Source: packages/db/prisma/schema.prisma:251

      id                  String    @id @default(uuid())
      enterpriseId        String
      userId              String
      role                String    @default("member")
      status              String    @default("active")
      workspaceQuotaBytes BigInt?
      realName            String?
      department          String?
      applicantNote       String?
      reviewNote          String?
      reviewedBy          String?
      reviewedAt          DateTime?
      joinedAt            DateTime?
      createdAt           DateTime  @default(now())
      updatedAt           DateTime  @updatedAt
      isDeleted           Boolean   @default(false)
      enterprise Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      user       User       @relation(fields: [userId], references: [id], onDelete: Cascade)
      @@unique([enterpriseId, userId, isDeleted])
      @@index([userId, status])
      @@index([enterpriseId, status])
      @@map("enterprise_memberships")
    }
## SkillCategory
Source: packages/db/prisma/schema.prisma:560

      id             String   @id @default(uuid())
      scope          String
      enterpriseId   String?
      name           String
      sortOrder      Int      @default(0)
      source         String   @default("custom")
      icon           String?
      colorClassName String?
      createdAt      DateTime @default(now())
      updatedAt      DateTime @updatedAt
      isDeleted      Boolean  @default(false)
      enterprise       Enterprise?             @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      globalSkills     GlobalSkillConfig[]
      enterpriseSkills EnterpriseSkillConfig[]
      skillSubmissions SkillSubmission[]
      @@index([scope, enterpriseId, isDeleted])
      @@map("skill_categories")
    }
## SkillSubmission
Source: packages/db/prisma/schema.prisma:582

      id                      String    @id @default(uuid())
      enterpriseId            String
      submitterUserId         String
      skillKey                String
      status                  String    @default("pending")
      title                   String
      description             String    @default("")
      filesSnapshot           Json
      targetUsers             String    @default("")
      reason                  String    @default("")
      exampleInput            String    @default("")
      prefillTemplate         String    @default("")
      expectedOutput          String    @default("")
      icon                    String?
      colorClassName          String?
      categoryId              String?
      categoryName            String?
      rejectReason            String    @default("")
      reviewedByUserId        String?
      reviewedAt              DateTime?
      version                 Int       @default(1)
      approvedVersionAtSubmit Int?
      sourceVersion           Int?
      createdAt               DateTime  @default(now())
      updatedAt               DateTime  @updatedAt
      isDeleted               Boolean   @default(false)
      enterprise Enterprise     @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      submitter  User           @relation("SkillSubmissionSubmitter", fields: [submitterUserId], references: [id], onDelete: Cascade)
      reviewer   User?          @relation("SkillSubmissionReviewer", fields: [reviewedByUserId], references: [id], onDelete: SetNull)
      category   SkillCategory? @relation(fields: [categoryId], references: [id], onDelete: SetNull)
      @@unique([enterpriseId, skillKey, submitterUserId])
      @@index([enterpriseId, status, isDeleted])
      @@index([submitterUserId, isDeleted])
      @@map("skill_submissions")
    }
## SkillSubmissionVersion
Source: packages/db/prisma/schema.prisma:621

      id              String    @id @default(uuid())
      enterpriseId    String
      submitterUserId String
      skillKey        String
      version         Int
      status          String    @default("approved")
      title           String
      description     String    @default("")
      filesSnapshot   Json
      targetUsers     String    @default("")
      reason          String    @default("")
      exampleInput    String    @default("")
      prefillTemplate String    @default("")
      expectedOutput  String    @default("")
      icon            String?
      colorClassName  String?
      sourceVersion   Int?
      approvedAt      DateTime?
      createdAt       DateTime  @default(now())
      updatedAt       DateTime  @updatedAt
      isDeleted       Boolean   @default(false)
      enterprise Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      @@unique([enterpriseId, submitterUserId, skillKey, version])
      @@index([enterpriseId, skillKey, isDeleted])
      @@map("skill_submission_versions")
    }
## PersonalSkillConfig
Source: packages/db/prisma/schema.prisma:651

      id              String   @id @default(uuid())
      enterpriseId    String
      userId          String
      skillKey        String
      title           String   @default("")
      description     String   @default("")
      targetUsers     String   @default("")
      reason          String   @default("")
      exampleInput    String   @default("")
      prefillTemplate String   @default("")
      expectedOutput  String   @default("")
      icon            String?
      colorClassName  String?
      /// Skill provenance; emergence installation verification requires skill_emergence.
      source          String   @default("manual")
      sourceRefId     String?
      /// Hidden from personal market / library until user confirms emergence draft.
      isVisible       Boolean  @default(true)
      /// Structured security assessment report (emergence packaging); JSON SkillReliabilityReport.
      reliabilityReport Json?
      createdAt       DateTime @default(now())
      updatedAt       DateTime @updatedAt
      isDeleted       Boolean  @default(false)
      enterprise Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      user       User       @relation(fields: [userId], references: [id], onDelete: Cascade)
      @@unique([enterpriseId, userId, skillKey])
      @@index([enterpriseId, userId, isDeleted])
      @@map("personal_skill_configs")
    }
## GlobalSkillConfig
Source: packages/db/prisma/schema.prisma:684

      id              String   @id @default(uuid())
      skillKey        String   @unique
      title           String
      description     String   @default("")
      targetUsers     String   @default("")
      reason          String   @default("")
      exampleInput    String   @default("")
      prefillTemplate String   @default("")
      expectedOutput  String   @default("")
      icon            String?
      colorClassName  String?
      categoryName    String?
      categoryId      String?
      sortOrder       Int      @default(0)
      isVisible       Boolean  @default(true)
      isHot           Boolean  @default(false)
      source          String   @default("admin_created")
      createdAt       DateTime @default(now())
      updatedAt       DateTime @updatedAt
      isDeleted       Boolean  @default(false)
      category SkillCategory? @relation(fields: [categoryId], references: [id], onDelete: SetNull)
      @@index([isDeleted, isVisible])
      @@map("global_skill_configs")
    }
## EnterpriseSkillConfig
Source: packages/db/prisma/schema.prisma:712

      id               String   @id @default(uuid())
      enterpriseId     String
      skillKey         String
      type             String
      title            String
      description      String   @default("")
      targetUsers      String   @default("")
      reason           String   @default("")
      exampleInput     String   @default("")
      prefillTemplate  String   @default("")
      expectedOutput   String   @default("")
      icon             String?
      colorClassName   String?
      categoryName     String?
      categoryId       String?
      sortOrder        Int      @default(0)
      isVisible        Boolean  @default(true)
      isHot            Boolean  @default(false)
      publishedVersion Int?
      createdAt        DateTime @default(now())
      updatedAt        DateTime @updatedAt
      isDeleted        Boolean  @default(false)
      enterprise Enterprise     @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
      category   SkillCategory? @relation(fields: [categoryId], references: [id], onDelete: SetNull)
      @@unique([enterpriseId, skillKey])
      @@index([enterpriseId, isDeleted, isVisible])
      @@map("enterprise_skill_configs")
    }
## SkillInventorySnapshot
Source: packages/db/prisma/schema.prisma:2295

      id           String   @id @default(uuid())
      enterpriseId String
      identityKey  String
      ownerUserId  String?
      skillKey     String
      skillName    String
      scope        String
      source       String
      categoryName String?
      firstSeenAt  DateTime @default(now())
      lastSeenAt   DateTime @default(now())
      isPresent    Boolean  @default(true)
      createdAt    DateTime @default(now())
      updatedAt    DateTime @updatedAt
      @@unique([enterpriseId, identityKey])
      @@index([enterpriseId, scope, isPresent])
      @@index([enterpriseId, firstSeenAt])
      @@index([ownerUserId, isPresent])
      @@map("skill_inventory_snapshots")
    }
## SkillUsageEvent
Source: packages/db/prisma/schema.prisma:2318

      id             String   @id @default(uuid())
      enterpriseId   String
      userId         String
      requestEventId String
      sessionId      String?
      skillKey       String
      skillName      String
      skillScope     String
      skillSource    String
      savedHours     Float    @default(0)
      occurredAt     DateTime @default(now())
      createdAt      DateTime @default(now())
      updatedAt      DateTime @updatedAt
      @@unique([enterpriseId, requestEventId, skillScope, skillKey])
      @@index([enterpriseId, occurredAt])
      @@index([enterpriseId, skillScope, skillKey, occurredAt])
      @@index([userId, occurredAt])
      @@map("skill_usage_events")
    }
## SkillEmergenceTaskCluster
Source: packages/db/prisma/schema.prisma:2340

      id                          String    @id @default(uuid())
      enterpriseId                String
      clusterKey                  String
      title                       String
      fingerprint                 Json
      workflow                    Json?
      confidence                  Float     @default(0)
      /// analysis: detected | path_processing | path_analyzed | path_failed
      status                      String    @default("detected")
      analysisAttempts            Int       @default(0)
      nextAnalysisAt              DateTime?
      lastError                   String?
      firstSeenAt                 DateTime  @default(now())
      lastSeenAt                  DateTime  @default(now())
      modeledAt                   DateTime?
      /// Evidence watermark: last packaged observation id / count / version
      lastPackagedObservationId   String?
      lastPackagedObservationAt   DateTime?
      lastPackagedObservationCount Int      @default(0)
      lastPackagedVersion         Int       @default(0)
      coveredBySkillKey           String?
      coveredAt                   DateTime?
      rejectCooldownUntil           DateTime?
      createdAt                   DateTime  @default(now())
      updatedAt                   DateTime  @updatedAt
      observations SkillEmergenceObservation[]
      evaluations  SkillEmergenceEvaluation[]
      candidates   SkillEmergenceCandidate[]
      packagingJobs SkillEmergencePackagingJob[]
      userProgress  SkillEmergenceUserProgress[]
      @@unique([enterpriseId, clusterKey])
      @@index([enterpriseId, status, lastSeenAt])
      @@index([status, nextAnalysisAt])
      @@map("skill_emergence_task_clusters")
    }
    /// Per-user packaging watermark / cover / reject cooldown (cluster fields are legacy analytics only).
## SkillEmergenceUserProgress
Source: packages/db/prisma/schema.prisma:2380

      id                           String    @id @default(uuid())
      clusterId                    String
      userId                       String
      enterpriseId                 String
      lastPackagedObservationCount Int       @default(0)
      lastPackagedObservationId    String?
      lastPackagedObservationAt    DateTime?
      coveredBySkillKey            String?
      coveredAt                    DateTime?
      rejectCooldownUntil          DateTime?
      createdAt                    DateTime  @default(now())
      updatedAt                    DateTime  @updatedAt
      cluster SkillEmergenceTaskCluster @relation(fields: [clusterId], references: [id], onDelete: Cascade)
      user    User                      @relation(fields: [userId], references: [id], onDelete: Cascade)
      @@unique([clusterId, userId])
      @@index([userId, enterpriseId])
      @@index([enterpriseId, clusterId])
      @@map("skill_emergence_user_progress")
    }
## SkillEmergenceObservation
Source: packages/db/prisma/schema.prisma:2403

      id                 String    @id @default(uuid())
      enterpriseId       String
      userId             String
      requestEventId     String
      sessionId          String
      userMessageId      String
      assistantMessageId String
      clusterId          String?
      status             String    @default("pending")
      /// SUCCESS | PARTIAL | FAILURE | UNKNOWN — gates count SUCCESS by default
      outcome            String    @default("UNKNOWN")
      attempts           Int       @default(0)
      nextAttemptAt      DateTime?
      lastError          String?
      messageCount       Int?
      effectiveCharCount Int?
      occurredAt         DateTime  @default(now())
      analyzedAt         DateTime?
      createdAt          DateTime  @default(now())
      updatedAt          DateTime  @updatedAt
      cluster  SkillEmergenceTaskCluster?      @relation(fields: [clusterId], references: [id], onDelete: SetNull)
      snapshot SkillEmergenceAnalysisSnapshot?
      @@unique([enterpriseId, requestEventId])
      @@index([status, nextAttemptAt, updatedAt])
      @@index([enterpriseId, occurredAt])
      @@index([clusterId, status, occurredAt])
      @@index([userId, enterpriseId, occurredAt])
      @@map("skill_emergence_observations")
    }
    /// Frozen analysis sample for path modeling — independent of live chat soft-delete.
## SkillEmergenceAnalysisSnapshot
Source: packages/db/prisma/schema.prisma:2437

      id                 String   @id @default(uuid())
      observationId      String   @unique
      userText           String   @db.Text
      assistantText      String   @db.Text
      messageCount       Int?
      effectiveCharCount Int?
      createdAt          DateTime @default(now())
      observation SkillEmergenceObservation @relation(fields: [observationId], references: [id], onDelete: Cascade)
      @@map("skill_emergence_analysis_snapshots")
    }
    /// Per user×enterprise evaluation schedule (alarm only; not a gate).
## SkillEmergenceScheduleState
Source: packages/db/prisma/schema.prisma:2452

      id               String    @id @default(uuid())
      userId           String
      enterpriseId     String
      nextEvaluationAt DateTime  @default(now())
      lastEvaluatedAt  DateTime?
      createdAt        DateTime  @default(now())
      updatedAt        DateTime  @updatedAt
      user User @relation(fields: [userId], references: [id], onDelete: Cascade)
      @@unique([userId, enterpriseId])
      @@index([nextEvaluationAt])
      @@map("skill_emergence_schedule_states")
    }
    /// One gate evaluation run — skip decisions are NOT cluster terminal states.
## SkillEmergenceEvaluation
Source: packages/db/prisma/schema.prisma:2469

      id               String   @id @default(uuid())
      clusterId        String
      userId           String
      enterpriseId     String
      evaluatedAt      DateTime @default(now())
      /// eligible | insufficient_signal | duplicate | covered | no_new_evidence | quota_blocked | disabled
      decision         String
      matchedGate      String?
      observationCount Int      @default(0)
      newEvidenceCount Int      @default(0)
      evidenceSnapshot Json?
      reason           String?
      createdAt        DateTime @default(now())
      cluster SkillEmergenceTaskCluster @relation(fields: [clusterId], references: [id], onDelete: Cascade)
      user    User                      @relation(fields: [userId], references: [id], onDelete: Cascade)
      @@index([clusterId, evaluatedAt])
      @@index([userId, enterpriseId, evaluatedAt])
      @@index([decision, evaluatedAt])
      @@map("skill_emergence_evaluations")
    }
    /// Skill draft candidate awaiting user confirm — separate from cluster lifecycle.
## SkillEmergenceCandidate
Source: packages/db/prisma/schema.prisma:2494

      id                   String    @id @default(uuid())
      clusterId            String
      userId               String
      enterpriseId         String
      /// DISCOVERED | CONFIRMING | PACKAGING | AWAITING_CONFIRM | INSTALLED | SUBMITTED | FAILED | REJECTED
      status               String    @default("DISCOVERED")
      matchedGate          String?
      confidence           String    @default("normal")
      summary              String?
      skillKey             String?
      skillTitle           String?
      draftFilesSnapshot   Json?
      /// Structured security assessment report generated after packaging.
      reliabilityReport    Json?
      evidenceFromCount    Int       @default(0)
      evidenceToCount      Int       @default(0)
      watermarkObservationId String?
      packagingJobId       String?
      acceptedSkillKey     String?
      confirmedAt          DateTime?
      rejectedAt           DateTime?
      acceptedAt           DateTime?
      createdAt            DateTime  @default(now())
      updatedAt            DateTime  @updatedAt
      cluster SkillEmergenceTaskCluster @relation(fields: [clusterId], references: [id], onDelete: Cascade)
      user    User                      @relation(fields: [userId], references: [id], onDelete: Cascade)
      packagingJobs SkillEmergencePackagingJob[]
      @@index([userId, enterpriseId, status, updatedAt])
      @@index([clusterId, status])
      @@index([status, updatedAt])
      @@unique([clusterId, userId, evidenceToCount])
      @@map("skill_emergence_candidates")
    }
## SkillEmergencePackagingJob
Source: packages/db/prisma/schema.prisma:2531

      id              String    @id @default(uuid())
      candidateId     String?
      clusterId       String
      userId          String
      enterpriseId    String
      /// queued | running | succeeded | failed | retryable | dead | cancelled
      status          String    @default("queued")
      idempotencyKey  String    @unique
      attemptCount    Int       @default(0)
      leaseUntil      DateTime?
      lastHeartbeatAt DateTime?
      billingTaskId   String?
      billingSettled  Boolean   @default(false)
      lastError       String?
      resultSkillKey  String?
      createdAt       DateTime  @default(now())
      updatedAt       DateTime  @updatedAt
      cluster   SkillEmergenceTaskCluster @relation(fields: [clusterId], references: [id], onDelete: Cascade)
      user      User                      @relation(fields: [userId], references: [id], onDelete: Cascade)
      candidate SkillEmergenceCandidate?  @relation(fields: [candidateId], references: [id], onDelete: SetNull)
      @@index([status, leaseUntil])
      @@index([clusterId, userId, status])
      @@map("skill_emergence_packaging_jobs")
    }
## UserSkillEmergencePreference
Source: packages/db/prisma/schema.prisma:2823

      id            String    @id @default(uuid())
      userId        String    @unique
      enabled       Boolean   @default(false)
      intervalDays  Int       @default(7)
      /// When true, packaged drafts auto-activate as personal Skills (skip user confirm).
      autoAcceptPersonal Boolean @default(false)
      enabledAt     DateTime?
      createdAt     DateTime  @default(now())
      updatedAt     DateTime  @updatedAt
      user User @relation(fields: [userId], references: [id], onDelete: Cascade)
      @@map("user_skill_emergence_preferences")
    }