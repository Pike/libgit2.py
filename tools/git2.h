#include "no-std.h"

# define GIT_EXTERN(type) extern type

GIT_EXTERN(void) git_libgit2_version(int *major, int *minor, int *rev);

#include "git2/errors.h"

typedef int64_t git_off_t;
typedef int64_t git_time_t;

typedef struct git_repository git_repository;

/** Size (in bytes) of a raw/binary oid */
#define GIT_OID_RAWSZ 20

/** Unique identity of any object (commit, tree, blob, tag). */
typedef struct git_oid {
	/** raw binary formatted id */
	unsigned char id[GIT_OID_RAWSZ];
} git_oid;

GIT_EXTERN(int) git_repository_open(git_repository **out, const char *path);

GIT_EXTERN(void) git_repository_free(git_repository *repo);

typedef int (*git_repository_mergehead_foreach_cb)(const git_oid *oid,
	void *payload);

/**
 * If a merge is in progress, call callback 'cb' for each commit ID in the
 * MERGE_HEAD file.
 *
 * @param repo A repository object
 * @param callback Callback function
 * @param apyload Pointer to callback data (optional)
 * @return 0 on success, GIT_ENOTFOUND, GIT_EUSER or error
 */
GIT_EXTERN(int) git_repository_mergehead_foreach(git_repository *repo,
	git_repository_mergehead_foreach_cb callback,
	void *payload);

GIT_EXTERN(int) git_merge_base_many(
	git_oid *out,
	git_repository *repo,
	const git_oid input_array[],
	size_t length);
