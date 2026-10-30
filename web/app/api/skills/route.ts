import { NextResponse, type NextRequest } from "next/server";

import { authorizedIdentity } from "@/lib/identity";
import { identityCookies } from "@/lib/request-identity";
import { listSkills } from "@/lib/skills";

/** The caller's installed skills (names and descriptions), for /command autocomplete. */
export async function GET(request: NextRequest) {
  const identity = await authorizedIdentity(identityCookies(request));
  if (!identity) {
    return NextResponse.json({ skills: [] });
  }
  const skills = await listSkills(identity.username);
  return NextResponse.json({
    skills: skills.map(({ name, description }) => ({ name, description })),
  });
}
