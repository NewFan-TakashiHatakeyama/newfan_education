import { redirect } from "next/navigation";

export default function PublicProfileRedirectPage() {
  redirect("/company/dashboard");
}
