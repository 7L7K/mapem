import { client } from '@lib/api/api';

export async function searchPeopleByName(uploadedTreeId: string, q: string) {
    const res = await client.get(`/api/people/${uploadedTreeId}`, { params: { person: q, limit: 25 } });
    return res.data?.people ?? [];
}


