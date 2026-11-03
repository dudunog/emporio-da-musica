import Image from "next/image";
import { AVATAR_ALT } from "../chat-copy";

const AVATAR_PATH = "/avatar.svg";
const AVATAR_PLACEMENTS = {
  bubble: { pixels: 28, sizeClass: "size-avatar-bubble" },
  header: { pixels: 36, sizeClass: "size-avatar-header" },
};

export function StoreAvatar({ placement }: Readonly<{ placement: keyof typeof AVATAR_PLACEMENTS }>) {
  const { pixels, sizeClass } = AVATAR_PLACEMENTS[placement];
  return (
    <Image
      src={AVATAR_PATH}
      alt={AVATAR_ALT}
      width={pixels}
      height={pixels}
      loading="eager"
      className={`shrink-0 rounded-full shadow-avatar ${sizeClass}`}
    />
  );
}
