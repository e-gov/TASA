"""TASA graphql"""

from typing import Tuple


def get_graphql_queries() -> str:
    """
    Retrieves the GraphQL queries for page and related data.

    Returns:
       Tuple[str]: The GraphQL queries for page and related data.
    """
    arva_records_query = """
        query($id: Int!) {
        pages {
            single(id: $id) {
            id
            title
            tags {
                id
                title
            }
            path
            content
            locale
            editor
            isPublished
            authorId
            authorName
            authorEmail
            creatorId
            creatorName
            creatorEmail
            createdAt
            updatedAt
            }
            history(id: $id) {
            trail {
                versionId
                versionDate
                authorId
                authorName
                actionType
                valueBefore
                valueAfter
            }
            total
            }
        }
        arvaInstitution {
            getArvaInstitutionsForPage(pageId: $id) {
            id
            name
            url
            isResponsible
            }
        }
        arvaLegalAct {
            getLegalActsForPage(pageId: $id) {
            id
            globalId
            groupId
            title
            url
            versionStartDate
            createdAt
            updatedAt
            legalActType
            }
        }
        arvaPageContact {
            getArvaPageContactForPage(pageId: $id) {
            id
            role
            firstName
            lastName
            contactId
            company
            email
            countryCode
            nationalNumber
            }
        }
        arvaRelatedPages {
            getRelatedPagesForPage(pageId: $id) {
            id
            title
            locale
            }
        }
        arvaService {
            getArvaServicesForPage(pageId: $id) {
            id
            name
            url
            }
        }
        arvaSdgMeta {
            getArvaSdgMetaForPage(pageId: $id) {
            id
            isSdg
            country
            serviceTypeCode
            nuts3Code
            lauCode
            annexiTopicsCode
            annexiiTopicsCode
            annexiiiServiceCode
            }
        }
        }
    """
    return arva_records_query


def get_graphql_mutations() -> Tuple[str, str, str]:
    """
    Retrieves the GraphQL mutations for creating a page and handling follow-ups.

    Returns:
        Tuple[str, str]: The create mutation and follow-up mutation strings.
    """
    create_mutation = """
        mutation (
            $content: String!,
            $description: String!,
            $editor: String!,
            $isPrivate: Boolean!,
            $isPublished: Boolean!,
            $locale: String!,
            $path: String!,
            $publishEndDate: Date,
            $publishStartDate: Date,
            $scriptCss: String,
            $scriptJs: String,
            $tags: [String]!,
            $title: String!
        ) {
        pages {
            create(
                content: $content,
                description: $description,
                editor: $editor,
                isPrivate: $isPrivate,
                isPublished: $isPublished,
                locale: $locale,
                path: $path,
                publishEndDate: $publishEndDate,
                publishStartDate: $publishStartDate,
                scriptCss: $scriptCss,
                scriptJs: $scriptJs,
                tags: $tags,
                title: $title
            ) {
            responseResult {
                succeeded
                errorCode
                slug
                message
                __typename
            }
            page {
                id
                updatedAt
                __typename
            }
            __typename
            }
            __typename
        }
        }
    """

    follow_up_mutation = """
        mutation (
            $pageId: Int!
            $institutionInput: [ArvaInstitutionInput]
            $legalActInput: [ArvaLegalActInput!]!
            $pageContactInput: [ArvaPageContactInput!]
            $relatedPagesInput: [ArvaRelatedPagesInput!]
            $serviceInput: [ArvaServiceInput!]
        ) {
            arvaInstitution {
                saveArvaInstitutionsForPage(pageId: $pageId, input: $institutionInput) {
                    succeeded
                    message
                    __typename
                }
            }
            arvaLegalAct {
                createArvaLegalAct(pageId: $pageId, input: $legalActInput) {
                    succeeded
                    message
                    __typename
                }
            }
            arvaPageContact {
                saveArvaPageContacts(pageId: $pageId, input: $pageContactInput) {
                    succeeded
                    message
                    __typename
                }
            }
            arvaRelatedPages {
                saveRelatedPages(pageId: $pageId, input: $relatedPagesInput) {
                    succeeded
                    message
                    __typename
                }
            }
            arvaService {
                saveArvaServicesForPage(pageId: $pageId, input: $serviceInput) {
                    succeeded
                    message
                    __typename
                }
            }
        }
    """

    update_mutation = """
        mutation (
            $id: Int!,
            $content: String!,
            $description: String!,
            $editor: String!,
            $isPrivate: Boolean!,
            $isPublished: Boolean!,
            $locale: String!,
            $path: String!,
            $publishEndDate: Date,
            $publishStartDate: Date,
            $scriptCss: String,
            $scriptJs: String,
            $tags: [String]!,
            $title: String!
        ) {
            pages {
                update(
                    id: $id,
                    content: $content,
                    description: $description,
                    editor: $editor,
                    isPrivate: $isPrivate,
                    isPublished: $isPublished,
                    locale: $locale,
                    path: $path,
                    publishEndDate: $publishEndDate,
                    publishStartDate: $publishStartDate,
                    scriptCss: $scriptCss,
                    scriptJs: $scriptJs,
                    tags: $tags,
                    title: $title
                ) {
                    responseResult {
                        succeeded
                        errorCode
                        slug
                        message
                        __typename
                    }
                    page {
                        id
                        updatedAt
                        __typename
                    }
                    __typename
                }
            }
        }
    """
    return create_mutation, follow_up_mutation, update_mutation
