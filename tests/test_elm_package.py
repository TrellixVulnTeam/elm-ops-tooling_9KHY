import elm_package


def test_sync_deps_messages_when_version_is_changed():
    from_deps = {'core': '1.0.0'}
    to_deps = {'core': '0.1.0'}

    messages, new_deps = elm_package.sync_deps(from_deps, to_deps)
    assert len(messages) == 1
    assert '0.1.0 to 1.0.0' in messages[0]
