from __future__ import annotations

from typing import TYPE_CHECKING
import time
import langdetect
import shortuuid
from langchain_groq import ChatGroq
from langchain_postgres.vectorstores import PGVector
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate

from langchain_ollama.chat_models import ChatOllama

if TYPE_CHECKING:
    from configuration_manager import ConfigurationManager
    from file_logger import FileLogger
    from os_environment_secret_manager import OsEnvironmentSecretManager


# noinspection DuplicatedCode
class LangchainLlmClient:

    def __init__(  # noqa: PLR0913
            self,
            logger: FileLogger,
            secret_manager: OsEnvironmentSecretManager,
            configuration_manager: ConfigurationManager,
            model: str,
            temperature: float,
            max_tokens: int,
            langchain_vector_store: PGVector,
            collection_name: str,
    ) -> None:
        super().__init__()
        self._logger = logger
        self._configuration_manager = configuration_manager
        self._secret_manager = secret_manager
        self._base_url = self._configuration_manager.get_value("langchain_llm_client.ollama_url")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._langchain_vector_store = langchain_vector_store
        self._collection_name = collection_name

        # if not os.getenv("ENVIRONMENT") == "local":

        # noinspection PyArgumentList
        self._LLM = ChatGroq(
            model="llama-3.2-1b-preview",
            temperature=temperature,  # 0-2
            max_tokens=max_tokens,
            max_retries=3,
            # top_p=0,  # 0-1
            # seed=12345,
            # stop="stop string",
            api_key=self._secret_manager.get_secret("GROQ_API_KEY")
        )

        # else:
        #     self._LLM = ChatOllama(
        #         base_url=self._base_url,
        #         model=self._model,
        #         temperature=self._temperature,
        #         num_predict=self._max_tokens,
        #         client_kwargs={"timeout": 60},
        #     )

    @staticmethod
    def _detect_language(text: str) -> str:
        try:
            language = langdetect.detect(text)
        except langdetect.lang_detect_exception.LangDetectException:
            language = None
        return language

    def ask_database(
            self,
            k: int,
            score_threshold: float,
            question: str,
    ) -> (str, str):

        start_time = time.perf_counter()
        # self._logger.info(f"ask_database started: {time.perf_counter() - start_time}")
        language = self._detect_language(question)

        raw_prompt = PromptTemplate.from_template(
            """
            <s>[INST] You are a helpful assistant. Think step by step.
            Use the provided context to answer the question.
            If the context does not contain the answer, say so.
            Be precise, no preamble, get to the point.
            [/INST]</s>
            [INST] {input}
                   Context: {context}
                   Answer:
            [/INST]
            """,
        )


        retriever_kwargs = {"k": k}

        search_type = "similarity_score_threshold"

        if search_type in ["mmr", "similarity_score_threshold"]:
            retriever_kwargs["score_threshold"] = (
                score_threshold)  # type: ignore

        retriever = self._langchain_vector_store.as_retriever(
            collection=self._collection_name,
            search_type=search_type,
            search_kwargs=retriever_kwargs,
            score_threshold=score_threshold,
        )

        # self._logger.info(f"Retriever created: {time.perf_counter() - start_time}")

        documents = retriever.get_relevant_documents(question)

        # self._logger.info(f"Documents received: {time.perf_counter() - start_time}")

        # if len(documents) == 0:
        #     return "No relevant information found. Please try asking something else.", shortuuid.uuid()

        context = "\n\n".join(doc.page_content for doc in documents)
        full_prompt = f"Question: {question}\n\nContext: {context}"
        # self._logger.info(f"Full prompt being sent to model:\n{full_prompt}")

        context_sources = ""

        source_file_names = []

        for document in documents:
            print(document.metadata["file_name"], flush=True)

            source_file_name = document.metadata["source_file_name"]

            if source_file_name not in source_file_names:
                source_file_names.append(source_file_name)

            context_sources += f"\n{document.metadata['source_file_name']}"
            context_sources += f"\n{document.metadata['file_name']}"
            context_sources += f"\n{document.page_content}"

        document_chain = create_stuff_documents_chain(self._LLM, raw_prompt)
        chain = create_retrieval_chain(retriever, document_chain)

        # self._logger.info(f"Chain created: {time.perf_counter() - start_time}")

        debug = False

        if not debug:
            try:

                # self._logger.info(f"Chain invoke: {time.perf_counter() - start_time}")
                result = chain.invoke(
                    {"input": question, "max_output_length": 1500},
                )
                # self._logger.info(f"Answer received: {time.perf_counter() - start_time}")

                answer = result["answer"]

            except Exception as e:
                answer = str(e)

        else:
            answer = f"{question}\n\n{100 * '-'}\n{context_sources}"

        # self._logger.info(f"Total execution time: {time.perf_counter() - start_time}")

        return answer, shortuuid.uuid()
