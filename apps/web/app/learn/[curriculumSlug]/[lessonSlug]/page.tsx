import { LearningLessonExperience } from "@/app/components/learning-template/LearningLessonExperience";
import { loadEnterpriseCurriculumBySlug } from "@/lib/curriculumMdx.server";

export default async function LessonDetailPage({
  params
}: {
  params: Promise<{ curriculumSlug: string; lessonSlug: string }>;
}) {
  const { curriculumSlug, lessonSlug } = await params;
  const curriculumModule = await loadEnterpriseCurriculumBySlug(curriculumSlug);

  return (
    <LearningLessonExperience
      curriculumSlug={curriculumSlug}
      lessonSlug={lessonSlug}
      content={
        curriculumModule
          ? {
              title: curriculumModule.title,
              skillTags: curriculumModule.skillTags,
              estimatedMinutes: curriculumModule.estimatedMinutes,
              week: curriculumModule.week,
              phase: curriculumModule.phase,
              deliverable: curriculumModule.deliverable,
              body: curriculumModule.body
            }
          : null
      }
    />
  );
}
