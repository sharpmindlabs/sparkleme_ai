import { useState } from "react";
import { imageUrl } from "../api";

/** A single thumbnail that removes itself from the layout if the image 404s
 *  (client has fewer than 5 drapes, or images aren't present in this env). */
function Thumb({ clientId, idx }: { clientId: string; idx: number }) {
  const [broken, setBroken] = useState(false);
  if (broken) return null;
  return (
    <img
      src={imageUrl(clientId, idx)}
      alt={`${clientId} drape ${idx + 1}`}
      loading="lazy"
      onError={() => setBroken(true)}
      className="h-12 w-12 shrink-0 rounded-md border border-slate-200 object-cover"
    />
  );
}

/** Strip of up to 5 drape thumbnails; broken/missing images are hidden. */
export default function Thumbnails({ clientId }: { clientId: string }) {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <Thumb key={i} clientId={clientId} idx={i} />
      ))}
    </div>
  );
}
