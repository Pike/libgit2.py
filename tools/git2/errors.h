/** Generic return codes */
enum {
	GIT_OK = 0,
	GIT_ERROR = -1
};


typedef struct {
	char *message;
	int klass;
} git_error;

/** Error classes */
typedef enum {
	GITERR_NOMEMORY,
	GITERR_OS
} git_error_t;

/**
 * Return the last `git_error` object that was generated for the
 * current thread or NULL if no error has occurred.
 *
 * @return A git_error object.
 */
GIT_EXTERN(const git_error *) giterr_last(void);
