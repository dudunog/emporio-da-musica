import Image from "next/image";
import { AVATAR_ALT } from "../chat-copy";

const AVATAR_PATH = "/avatar.svg";

type StoreAvatarProps = Readonly<{
  size: number;
  className: string;
}>;

export function StoreAvatar({ size, className }: StoreAvatarProps) {
  return (
    <Image
      src={AVATAR_PATH}
      alt={AVATAR_ALT}
      width={size}
      height={size}
      loading="eager"
      className={`shrink-0 rounded-full shadow-avatar ${className}`}
    />
  );
}
