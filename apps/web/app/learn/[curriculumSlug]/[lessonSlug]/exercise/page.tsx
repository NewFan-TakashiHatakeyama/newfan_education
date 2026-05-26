"use client";

import { useParams } from "next/navigation";
import { LearningExerciseWorkspace } from "@/app/components/learning-template/LearningExerciseWorkspace";

export default function ExercisePage() {
  const params = useParams<{ curriculumSlug: string; lessonSlug: string }>();
  const lessonSlug = params.lessonSlug ?? "unknown-lesson";
  const curriculumSlug = params.curriculumSlug ?? "unknown-curriculum";

  return <LearningExerciseWorkspace curriculumSlug={curriculumSlug} lessonSlug={lessonSlug} />;
}
